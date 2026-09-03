# MT Dashboard — Peliqan API handler (reference)
# Mirrors logic from documentation/PELIQAN_MT_DASHBOARD.md (Streamlit).
#
# Peliqan: App type "API endpoint handler", link GET route (e.g. /mt/data).
# Query params:
#   bundle   = cashweb | hubspot | sprinter | all   (default: all)
#   book_year = e.g. 2026                         (default: current calendar year)
#   month    = 1-12 | all                         (default: all = YTD for current book_year,
#                                                 full 12 months for past book years)
#   quarter  = 1-4 | all                         (winrate closedate window; default: all)
#   wage_accounts = JSON object                    (optional; loonrekeningen per admin_code)
#   start_date / end_date = YYYY-MM-DD          (optional; HubSpot + Sprinter + deal date filters)
#                                                 default: Jan 1 book_year → today
#
# Warehouse id must match Peliqan (see sidebar in Streamlit doc: dw_2401).

import json
import calendar
from datetime import date, datetime
from urllib.parse import parse_qs

import pandas as pd

WAREHOUSE_DW = "dw_2401"

CW_AMOUNT = """CAST(
    NULLIF(
        REPLACE(REPLACE(TRIM(COALESCE(amount, '')), '.', ''), ',', '.'),
        ''
    ) AS NUMERIC
)"""
CW_IS_D = "UPPER(TRIM(COALESCE(debit_credit, ''))) IN ('D', 'DEBET', 'DEBIT')"
CW_IS_C = "UPPER(TRIM(COALESCE(debit_credit, ''))) IN ('C', 'CREDIT')"
CW_IS_NULL = "NULLIF(TRIM(COALESCE(debit_credit, '')), '') IS NULL"
CW_OMZET_DAGBOEKEN = "('50', 'VERK')"

# Brief Fonkel deel 1 — keep in sync with config/mt_kpi.php
MT_KPI_CONFIG = {
    "entities": {
        "alaw": {"label": "AWC", "close_lag_months": 1},
        "pgl1": {"label": "AFC", "close_lag_months": 2},
        "acco": {"label": "ACC", "close_lag_months": 1},
    },
    "excluded_admin_codes": ["demo"],
    "wage_accounts": {
        "alaw": ["4000", "4001", "4010", "40100", "40101", "4110", "4130", "4514"],
        "pgl1": ["4010", "4011", "4110", "41100", "4130", "4512", "4514"],
        "acco": ["4010", "4011", "4110", "41100", "4130", "4512", "4514"],
    },
    "partial_wage_accounts": ["4130", "4512"],
    "winrate_validation": {
        "Verkooppijplijn": {"won": 55, "lost": 148, "pct": 27.1},
        "AFC Verkooplijn": {"won": 16, "lost": 8, "pct": 66.7},
    },
}

_dbconn = pq.dbconnect(WAREHOUSE_DW)


def df_records(df):
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def fetch(query, _label="q"):
    try:
        df = _dbconn.fetch(WAREHOUSE_DW, query=query, df=True)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def cw_periode_filter(jaar, bp_str):
    return f"book_year = '{jaar}' AND CAST(book_period AS INTEGER) IN ({bp_str})"


def month_end(y, m):
    return date(y, m, calendar.monthrange(y, m)[1])


def add_years(d, delta_years):
    """Shift calendar date by years (handles Feb 29)."""
    try:
        return date(d.year + delta_years, d.month, d.day)
    except ValueError:
        return date(
            d.year + delta_years,
            d.month,
            calendar.monthrange(d.year + delta_years, d.month)[1],
        )


def cashweb_months(book_year_int, month_raw, end_date):
    """
    Cashweb book_period months for YoY comparison.

    - month = 1-12  → that month only
    - month = all   → past book years: Jan–Dec
                      current book year: YTD through end_date (or today)
    """
    mlow = str(month_raw).lower().strip()
    if mlow not in ("", "all", "*"):
        m = int(month_raw)
        return [m], "month"

    today = date.today()
    if book_year_int < today.year:
        return list(range(1, 13)), "full_year"
    if book_year_int > today.year:
        return list(range(1, 13)), "full_year"

    if end_date.year == book_year_int:
        anchor_month = end_date.month
    elif today.year == book_year_int:
        anchor_month = today.month
    else:
        anchor_month = 12

    return list(range(1, anchor_month + 1)), "ytd"


def period_label(book_year, maanden_filter, mode):
    """Human-readable period for API filters (MT dashboard)."""
    if not maanden_filter:
        return str(book_year)
    if mode == "month":
        return f"{book_year} · periode {maanden_filter[0]:02d}"
    if mode == "full_year":
        return f"{book_year} · heel jaar (12 periodes)"
    first, last = maanden_filter[0], maanden_filter[-1]
    if first == last:
        return f"{book_year} · YTD periode {first:02d}"
    return f"{book_year} · YTD periodes {first:02d}–{last:02d}"


def parse_query(request):
    """Flatten Peliqan request into a dict of query params."""
    out = {}
    if request is None:
        return out
    if isinstance(request, dict):
        if isinstance(request.get("query"), dict):
            out.update({k: v[0] if isinstance(v, list) and v else v for k, v in request["query"].items()})
        elif isinstance(request.get("query_params"), dict):
            out.update(request["query_params"])
        qs = request.get("query_string") or request.get("queryString") or ""
        if isinstance(qs, str) and qs.strip():
            for k, v in parse_qs(qs.lstrip("?")).items():
                if v:
                    out.setdefault(k, v[0])
    else:
        if hasattr(request, "args"):
            for k in request.args:
                out[k] = request.args.get(k)
    return out


def parse_wage_accounts(q):
    """Optional JSON override via ?wage_accounts={...} from Laravel config."""
    raw = q.get("wage_accounts")
    if raw:
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return MT_KPI_CONFIG["wage_accounts"]


def quarter_window(book_year_int, quarter_raw, end_date):
    """Closedate window for winrate (Brief: per kwartaal op closedate)."""
    q = str(quarter_raw or "all").lower().strip()
    if q in ("1", "2", "3", "4"):
        qi = int(q)
        start_month = (qi - 1) * 3 + 1
        end_month = qi * 3
        wr_start = date(book_year_int, start_month, 1)
        wr_end = month_end(book_year_int, end_month)
        return wr_start, wr_end, f"Q{qi} {book_year_int}"
    today = date.today()
    wr_start = date(book_year_int, 1, 1)
    if book_year_int < today.year:
        wr_end = date(book_year_int, 12, 31)
        lbl = f"Heel jaar {book_year_int}"
    elif book_year_int > today.year:
        wr_end = date(book_year_int, 12, 31)
        lbl = f"Heel jaar {book_year_int}"
    else:
        wr_end = min(end_date, today)
        lbl = f"YTD {book_year_int}"
    return wr_start, wr_end, lbl


def sql_in_list(values):
    return ", ".join("'" + str(v).replace("'", "''") + "'" for v in values)


def sql_winrate_by_pipeline(start_iso, end_iso):
    return f"""
    SELECT
        d.pipeline AS pipeline_id,
        COALESCE(p.label, CAST(d.pipeline AS TEXT), '—') AS pipeline_label,
        SUM(CASE WHEN d.hs_is_closed_won = 'true' THEN 1 ELSE 0 END) AS gewonnen,
        SUM(CASE WHEN d.hs_is_closed_lost = 'true' THEN 1 ELSE 0 END) AS verloren
    FROM hubspot_v2.deals d
    LEFT JOIN hubspot_v2.deals_pipeline p ON d.pipeline = p.id
    WHERE d.closedate >= '{start_iso}'
      AND d.closedate <= '{end_iso}'
    GROUP BY d.pipeline, p.label
    ORDER BY pipeline_label
    """


def sql_winrate_validation():
    return """
    SELECT
        COALESCE(p.label, CAST(d.pipeline AS TEXT), '—') AS pipeline_label,
        SUM(CASE WHEN d.hs_is_closed_won = 'true' THEN 1 ELSE 0 END) AS gewonnen,
        SUM(CASE WHEN d.hs_is_closed_lost = 'true' THEN 1 ELSE 0 END) AS verloren
    FROM hubspot_v2.deals d
    LEFT JOIN hubspot_v2.deals_pipeline p ON d.pipeline = p.id
    GROUP BY d.pipeline, p.label
    ORDER BY pipeline_label
    """


def build_winrate_rows(df):
    rows = []
    if df is None or df.empty:
        return rows
    for _, r in df.iterrows():
        won = int(safe_float(r.get("gewonnen")))
        lost = int(safe_float(r.get("verloren")))
        denom = won + lost
        pct = round(won / denom * 100, 1) if denom > 0 else None
        rows.append({
            "pipeline_id": r.get("pipeline_id"),
            "pipeline_label": str(r.get("pipeline_label") or "—"),
            "gewonnen": won,
            "verloren": lost,
            "winrate_pct": pct,
        })
    return rows


def period_month_from_bp(bp):
    try:
        return int(bp) % 100
    except Exception:
        return None


def month_is_definitief(admin_code, book_year_int, book_period_int, today=None):
    today = today or date.today()
    month = period_month_from_bp(book_period_int)
    if not month:
        return False
    lag = MT_KPI_CONFIG["entities"].get(admin_code, {}).get("close_lag_months", 1)
    target_month = month + lag
    target_year = book_year_int
    while target_month > 12:
        target_month -= 12
        target_year += 1
    return today > month_end(target_year, target_month)


def sql_marge_per_loon_monthly(book_year, wage_accounts):
    entity_codes = list(MT_KPI_CONFIG["entities"].keys())
    excluded = MT_KPI_CONFIG["excluded_admin_codes"]
    admin_in = sql_in_list(entity_codes)
    admin_not = sql_in_list(excluded)
    partial = MT_KPI_CONFIG["partial_wage_accounts"]

    wage_case_parts = []
    for admin, accounts in wage_accounts.items():
        if not accounts:
            continue
        acct_in = sql_in_list(accounts)
        wage_case_parts.append(
            f"WHEN admin_code = '{admin}' "
            f"AND TRIM(COALESCE(account_number, '')) IN ({acct_in}) "
            f"AND ({CW_IS_D} OR {CW_IS_NULL}) THEN "
            f"CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE {CW_AMOUNT} END"
        )
    wage_case = (
        "SUM(CASE " + " ".join(wage_case_parts) + " ELSE 0 END)"
        if wage_case_parts
        else "0"
    )

    partial_cols = []
    for acct in partial:
        partial_cols.append(
            f"SUM(CASE WHEN TRIM(COALESCE(account_number, '')) = '{acct}' "
            f"AND ({CW_IS_D} OR {CW_IS_NULL}) THEN "
            f"CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE {CW_AMOUNT} END "
            f"ELSE 0 END) AS acct_{acct}"
        )
    partial_sql = ",\n        ".join(partial_cols) if partial_cols else ""

    return f"""
    SELECT
        admin_code,
        CAST(book_period AS INTEGER) AS book_period,
        SUM(CASE WHEN TRIM(COALESCE(account_number, '')) LIKE '8%'
                      AND ({CW_IS_C} OR {CW_IS_NULL}) THEN
            CASE WHEN {CW_IS_C} THEN {CW_AMOUNT} ELSE -({CW_AMOUNT}) END
            ELSE 0 END) AS omzet,
        SUM(CASE WHEN TRIM(COALESCE(account_number, '')) LIKE '6%'
                      AND ({CW_IS_D} OR {CW_IS_NULL}) THEN
            CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE {CW_AMOUNT} END
            ELSE 0 END) AS inkoop,
        {wage_case} AS loonkosten
        {',' if partial_sql else ''}
        {partial_sql}
    FROM cashweb.ledger_mutations
    WHERE book_year = '{book_year}'
      AND admin_code IN ({admin_in})
      AND admin_code NOT IN ({admin_not})
    GROUP BY admin_code, CAST(book_period AS INTEGER)
    ORDER BY admin_code, book_period
    """


def build_marge_per_loon(df_monthly, book_year_int, wage_accounts):
    entities_cfg = MT_KPI_CONFIG["entities"]
    partial_accts = MT_KPI_CONFIG["partial_wage_accounts"]
    today = date.today()

    by_admin = {}
    for admin in entities_cfg:
        by_admin[admin] = {
            "admin_code": admin,
            "label": entities_cfg[admin]["label"],
            "bruto_marge": 0.0,
            "loonkosten": 0.0,
            "kpi": None,
            "months": [],
            "partial_wage": {a: 0.0 for a in partial_accts},
        }

    if df_monthly is not None and not df_monthly.empty:
        for _, r in df_monthly.iterrows():
            admin = str(r.get("admin_code") or "").strip()
            if admin not in by_admin:
                continue
            bp = int(safe_float(r.get("book_period")))
            omzet = safe_float(r.get("omzet"))
            inkoop = safe_float(r.get("inkoop"))
            loon = safe_float(r.get("loonkosten"))
            marge = omzet - inkoop
            kpi = round(marge / loon, 2) if loon > 0 else None
            definitief = month_is_definitief(admin, book_year_int, bp, today)
            month_row = {
                "book_period": bp,
                "month": period_month_from_bp(bp),
                "omzet": round(omzet, 2),
                "inkoop": round(inkoop, 2),
                "bruto_marge": round(marge, 2),
                "loonkosten": round(loon, 2),
                "kpi": kpi,
                "definitief": definitief,
            }
            for acct in partial_accts:
                col = f"acct_{acct}"
                if col in r.index:
                    val = safe_float(r.get(col))
                    month_row[f"acct_{acct}"] = round(val, 2)
                    by_admin[admin]["partial_wage"][acct] += val
            by_admin[admin]["months"].append(month_row)
            if definitief:
                by_admin[admin]["bruto_marge"] += marge
                by_admin[admin]["loonkosten"] += loon

    entities = []
    tot_marge = 0.0
    tot_loon = 0.0
    for admin, row in by_admin.items():
        row["bruto_marge"] = round(row["bruto_marge"], 2)
        row["loonkosten"] = round(row["loonkosten"], 2)
        row["kpi"] = (
            round(row["bruto_marge"] / row["loonkosten"], 2)
            if row["loonkosten"] > 0
            else None
        )
        row["partial_wage"] = {
            k: round(v, 2) for k, v in row["partial_wage"].items()
        }
        row["wage_accounts"] = wage_accounts.get(admin, [])
        entities.append(row)
        tot_marge += row["bruto_marge"]
        tot_loon += row["loonkosten"]

    return {
        "entities": entities,
        "totals": {
            "bruto_marge": round(tot_marge, 2),
            "loonkosten": round(tot_loon, 2),
            "kpi": round(tot_marge / tot_loon, 2) if tot_loon > 0 else None,
        },
        "method": "account_prefix_8_6",
        "partial_wage_accounts": partial_accts,
    }


def build_params(q):
    book_year = str(q.get("book_year") or datetime.today().year)
    book_year_int = int(book_year)
    month_raw = q.get("month") or "all"
    quarter_raw = q.get("quarter") or "all"
    wage_accounts = parse_wage_accounts(q)

    start_s = q.get("start_date")
    end_s = q.get("end_date")
    if start_s:
        start_date = datetime.strptime(str(start_s)[:10], "%Y-%m-%d").date()
    else:
        start_date = date(book_year_int, 1, 1)
    if end_s:
        end_date = datetime.strptime(str(end_s)[:10], "%Y-%m-%d").date()
    else:
        end_date = date.today()

    maanden_filter, comparison_mode = cashweb_months(
        book_year_int, month_raw, end_date
    )
    if not maanden_filter:
        maanden_filter = [1]
        comparison_mode = "month"

    _yy = int(str(book_year)[-2:])
    book_periods = [_yy * 100 + m for m in maanden_filter]
    bp_str = ", ".join(str(p) for p in book_periods)
    _yy_v = _yy - 1
    book_periods_v = [_yy_v * 100 + m for m in maanden_filter]
    bp_v_str = ", ".join(str(p) for p in book_periods_v)
    boekjaar_v = str(book_year_int - 1)
    laatste_m = maanden_filter[-1]

    # HubSpot / Sprinter: same calendar window, shifted one year back (like-for-like)
    prev_start = add_years(start_date, -1)
    prev_end = add_years(end_date, -1)

    wr_start, wr_end, wr_label = quarter_window(book_year_int, quarter_raw, end_date)
    wr_prev_start = add_years(wr_start, -1)
    wr_prev_end = add_years(wr_end, -1)

    cw_f = cw_periode_filter(book_year, bp_str)
    cw_f_v = cw_periode_filter(boekjaar_v, bp_v_str)

    period_lbl = period_label(book_year, maanden_filter, comparison_mode)
    yoy_lbl = (
        f"{start_date.isoformat()} → {end_date.isoformat()} vs "
        f"{prev_start.isoformat()} → {prev_end.isoformat()}"
    )

    return {
        "book_year": book_year,
        "boekjaar_v": boekjaar_v,
        "maanden_filter": maanden_filter,
        "bp_str": bp_str,
        "bp_v_str": bp_v_str,
        "laatste_m": laatste_m,
        "comparison_mode": comparison_mode,
        "period_label": period_lbl,
        "yoy_label": yoy_lbl,
        "start_date": start_date,
        "end_date": end_date,
        "start_iso": start_date.isoformat(),
        "end_iso": end_date.isoformat(),
        "prev_start_iso": prev_start.isoformat(),
        "prev_end_iso": prev_end.isoformat(),
        "quarter": str(quarter_raw),
        "winrate_start_iso": wr_start.isoformat(),
        "winrate_end_iso": wr_end.isoformat(),
        "winrate_prev_start_iso": wr_prev_start.isoformat(),
        "winrate_prev_end_iso": wr_prev_end.isoformat(),
        "winrate_period_label": wr_label,
        "wage_accounts": wage_accounts,
        "cw_filter": cw_f,
        "cw_filter_v": cw_f_v,
    }


def sql_omzet(cw_f):
    return """
SELECT
    admin_code,
    sub_administration,
    journal_code,
    SUM(CASE WHEN {is_d} THEN {amt} ELSE 0 END) AS debet,
    SUM(CASE WHEN {is_c} THEN {amt} ELSE 0 END) AS credit,
    COUNT(*) AS mutaties
FROM cashweb.ledger_mutations
WHERE {periode}
  AND journal_code IN {dagboeken}
GROUP BY admin_code, sub_administration, journal_code
ORDER BY admin_code, journal_code
""".format(
        is_d=CW_IS_D, is_c=CW_IS_C, amt=CW_AMOUNT,
        periode=cw_f, dagboeken=CW_OMZET_DAGBOEKEN,
    )


def sql_omzet_v(cw_f_v):
    return """
SELECT
    admin_code,
    SUM(CASE WHEN {is_d} THEN {amt} ELSE 0 END) AS debet_v,
    SUM(CASE WHEN {is_c} THEN {amt} ELSE 0 END) AS credit_v
FROM cashweb.ledger_mutations
WHERE {periode}
  AND journal_code IN {dagboeken}
GROUP BY admin_code
""".format(
        is_d=CW_IS_D, is_c=CW_IS_C, amt=CW_AMOUNT,
        periode=cw_f_v, dagboeken=CW_OMZET_DAGBOEKEN,
    )


LOB_KEY = (
    "COALESCE(NULLIF(TRIM(sub_administration), ''), "
    "NULLIF(TRIM(admin_code), ''), '—')"
)


def sql_omzet_by_lob(cw_f):
    return f"""
SELECT
    {LOB_KEY} AS lob,
    MIN(admin_code) AS admin_code,
    SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet
FROM cashweb.ledger_mutations
WHERE {cw_f}
  AND journal_code IN {CW_OMZET_DAGBOEKEN}
GROUP BY {LOB_KEY}
ORDER BY omzet DESC
"""


def sql_omzet_by_lob_v(cw_f_v):
    return f"""
SELECT
    {LOB_KEY} AS lob,
    MIN(admin_code) AS admin_code,
    SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet_vorig
FROM cashweb.ledger_mutations
WHERE {cw_f_v}
  AND journal_code IN {CW_OMZET_DAGBOEKEN}
GROUP BY {LOB_KEY}
ORDER BY omzet_vorig DESC
"""


def build_revenue_per_lob(df_cur, df_v):
    cur = {}
    admin = {}
    if df_cur is not None and not df_cur.empty:
        for _, r in df_cur.iterrows():
            lob = str(r.get("lob") or "—").strip() or "—"
            cur[lob] = cur.get(lob, 0.0) + safe_float(r.get("omzet"))
            if lob not in admin and r.get("admin_code"):
                admin[lob] = str(r.get("admin_code"))

    prev = {}
    if df_v is not None and not df_v.empty:
        for _, r in df_v.iterrows():
            lob = str(r.get("lob") or "—").strip() or "—"
            prev[lob] = prev.get(lob, 0.0) + safe_float(r.get("omzet_vorig"))

    all_lobs = set(cur) | set(prev)
    tot = sum(cur.values())
    tot_v = sum(prev.values())
    rows = []
    for lob in sorted(all_lobs, key=lambda l: cur.get(l, 0.0), reverse=True):
        o = cur.get(lob, 0.0)
        o_v = prev.get(lob, 0.0)
        delta = None
        if o_v:
            delta = round((o - o_v) / abs(o_v) * 100, 1)
        rows.append({
            "lob": lob,
            "admin_code": admin.get(lob, ""),
            "omzet": round(o, 2),
            "omzet_vorig": round(o_v, 2),
            "aandeel_pct": round(o / tot * 100, 1) if tot > 0 else 0.0,
            "delta_pct": delta,
        })

    delta_totaal = None
    if tot_v:
        delta_totaal = round((tot - tot_v) / abs(tot_v) * 100, 1)

    return {
        "rows": rows,
        "totaal": round(tot, 2),
        "totaal_vorig": round(tot_v, 2),
        "delta_totaal_pct": delta_totaal,
        "lob_field": "sub_administration (fallback: admin_code)",
    }


def build_revenue_per_lob_monthly(df):
    by_lob = {}
    if df is not None and not df.empty:
        for _, r in df.iterrows():
            lob = str(r.get("lob") or "—").strip() or "—"
            bp = int(safe_float(r.get("book_period")))
            omzet = safe_float(r.get("omzet"))
            entry = by_lob.setdefault(
                lob,
                {"lob": lob, "admin_code": "", "months": []},
            )
            if not entry["admin_code"] and r.get("admin_code"):
                entry["admin_code"] = str(r.get("admin_code"))
            entry["months"].append({
                "book_period": bp,
                "month": period_month_from_bp(bp),
                "omzet": round(omzet, 2),
            })
    for entry in by_lob.values():
        entry["months"].sort(key=lambda m: m["book_period"])
    return sorted(
        by_lob.values(),
        key=lambda e: sum(m["omzet"] for m in e["months"]),
        reverse=True,
    )


def sql_omzet_by_lob_monthly(book_year):
    return f"""
SELECT
    {LOB_KEY} AS lob,
    MIN(admin_code) AS admin_code,
    CAST(book_period AS INTEGER) AS book_period,
    SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet
FROM cashweb.ledger_mutations
WHERE book_year = '{book_year}'
  AND journal_code IN {CW_OMZET_DAGBOEKEN}
GROUP BY {LOB_KEY}, CAST(book_period AS INTEGER)
ORDER BY lob, book_period
"""


def sql_ink(cw_f):
    return """
SELECT
    admin_code,
    SUM(CASE WHEN {is_c} THEN {amt} ELSE 0 END) AS credit_ink,
    COUNT(*) AS mutaties
FROM cashweb.ledger_mutations
WHERE {periode}
  AND journal_code = 'INK'
GROUP BY admin_code
""".format(is_c=CW_IS_C, amt=CW_AMOUNT, periode=cw_f)


def sql_sal(cw_f):
    return """
SELECT
    admin_code,
    book_period,
    SUM(CASE WHEN {is_d} THEN {amt} ELSE 0 END) AS loon_debet,
    SUM(CASE WHEN {is_c} THEN {amt} ELSE 0 END) AS loon_credit,
    COUNT(*) AS mutaties,
    COUNT(DISTINCT relation_number) AS unieke_relaties
FROM cashweb.ledger_mutations
WHERE {periode}
  AND journal_code = 'SAL'
GROUP BY admin_code, book_period
ORDER BY admin_code, book_period
""".format(is_d=CW_IS_D, is_c=CW_IS_C, amt=CW_AMOUNT, periode=cw_f)


def sql_omzet_trend(book_year):
    return f"""
SELECT
    admin_code,
    CAST(book_period AS INTEGER) AS periode,
    SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet
FROM cashweb.ledger_mutations
WHERE book_year = '{book_year}'
  AND journal_code IN {CW_OMZET_DAGBOEKEN}
GROUP BY admin_code, CAST(book_period AS INTEGER)
ORDER BY periode
"""


def sql_journal_breakdown(cw_f):
    return f"""
    SELECT journal_code, admin_code,
           COUNT(*) AS mutaties,
           SUM({CW_AMOUNT}) AS totaal_bedrag
    FROM cashweb.ledger_mutations
    WHERE {cw_f}
    GROUP BY journal_code, admin_code
    ORDER BY mutaties DESC
"""


def sql_balances(book_year):
    # Raw period columns — can contain ~ lists; do not CAST (see AWC ledger_balances fix).
    return f"""
    SELECT
        admin_code,
        account_number,
        description,
        exploitation_code,
        book_year,
        period_amounts_debit,
        period_amounts_credit,
        period_amounts_result
    FROM cashweb.ledger_balances
    WHERE book_year = '{book_year}'
      AND account_number IS NOT NULL
    ORDER BY admin_code, account_number
"""


def sql_triple_lob(book_year):
    return f"""
    SELECT
        relation_number,
        COUNT(DISTINCT sub_administration) AS aantal_lob,
        SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet,
        MIN(admin_code) AS admin_code
    FROM cashweb.ledger_mutations
    WHERE book_year = '{book_year}'
      AND journal_code IN {CW_OMZET_DAGBOEKEN}
      AND relation_number IS NOT NULL AND relation_number != ''
    GROUP BY relation_number
"""


def sql_sub_admin_dist(cw_f):
    return f"""
    SELECT sub_administration, admin_code, COUNT(*) AS mutaties
    FROM cashweb.ledger_mutations
    WHERE {cw_f}
    GROUP BY sub_administration, admin_code
    ORDER BY mutaties DESC
"""


def safe_float(x, default=0.0):
    try:
        return float(str(x).replace(",", ".").replace(" ", "")) if x is not None else default
    except Exception:
        return default


def bundle_cashweb(p):
    df_omzet = fetch(sql_omzet(p["cw_filter"]), "cw_omzet")
    df_omzet_v = fetch(sql_omzet_v(p["cw_filter_v"]), "cw_omzet_v")
    df_ink = fetch(sql_ink(p["cw_filter"]), "cw_ink")
    df_ink_v = fetch(sql_ink(p["cw_filter_v"]), "cw_ink_v")
    df_sal = fetch(sql_sal(p["cw_filter"]), "cw_sal")
    df_admins = fetch(
        """SELECT DISTINCT admin_code FROM cashweb.ledger_mutations
           WHERE admin_code IS NOT NULL AND admin_code != ''""",
        "admins",
    )
    df_trend = fetch(sql_omzet_trend(p["book_year"]), "fin_trend")
    df_jc = fetch(sql_journal_breakdown(p["cw_filter"]), "dagboeken")
    df_bal = fetch(sql_balances(p["book_year"]), "balances")
    df_triple = fetch(sql_triple_lob(p["book_year"]), "triple")
    df_sub = fetch(sql_sub_admin_dist(p["cw_filter"]), "subadm")
    df_lob = fetch(sql_omzet_by_lob(p["cw_filter"]), "omzet_lob")
    df_lob_v = fetch(sql_omzet_by_lob_v(p["cw_filter_v"]), "omzet_lob_v")
    df_lob_m = fetch(sql_omzet_by_lob_monthly(p["book_year"]), "omzet_lob_m")
    revenue_lob = build_revenue_per_lob(df_lob, df_lob_v)
    revenue_lob["monthly_by_lob"] = build_revenue_per_lob_monthly(df_lob_m)

    df_mpl = fetch(
        sql_marge_per_loon_monthly(p["book_year"], p["wage_accounts"]),
        "marge_per_loon",
    )
    marge_per_loon = build_marge_per_loon(
        df_mpl, int(p["book_year"]), p["wage_accounts"]
    )

    tot_omzet = df_omzet["debet"].apply(safe_float).sum() if not df_omzet.empty else 0.0
    tot_omzet_v = df_omzet_v["debet_v"].apply(safe_float).sum() if not df_omzet_v.empty else 0.0
    tot_ink = abs(df_ink["credit_ink"].apply(safe_float).sum()) if not df_ink.empty else 0.0
    tot_ink_v = abs(df_ink_v["credit_ink"].apply(safe_float).sum()) if not df_ink_v.empty else 0.0

    return {
        "aggregates": {
            "omzet": tot_omzet,
            "omzet_vorig": tot_omzet_v,
            "inkoop": tot_ink,
            "inkoop_vorig": tot_ink_v,
            "brutomarge": tot_omzet - tot_ink,
            "brutomarge_vorig": tot_omzet_v - tot_ink_v,
            "marge_pct": round((tot_omzet - tot_ink) / tot_omzet * 100, 2) if tot_omzet > 0 else 0,
        },
        "omzet_detail": df_records(df_omzet),
        "omzet_vorig_per_admin": df_records(df_omzet_v),
        "inkoop_per_admin": df_records(df_ink),
        "inkoop_vorig_per_admin": df_records(df_ink_v),
        "salarissen_SAL": df_records(df_sal),
        "admin_codes": df_records(df_admins),
        "omzet_trend_per_maand": df_records(df_trend),
        "journal_breakdown": df_records(df_jc),
        "ledger_balances": df_records(df_bal),
        "triple_lob_customers": df_records(df_triple),
        "sub_administration_dist": df_records(df_sub),
        "revenue_per_lob": revenue_lob,
        "marge_per_loon": marge_per_loon,
    }


def bundle_sprinter(p):
    s, e = p["start_iso"], p["end_iso"]
    ps, pe = p["prev_start_iso"], p["prev_end_iso"]

    df_ship = fetch(f"""
    SELECT
        s.shipment_id, s.shipment_number, s.report_date,
        s.shipment_mode, s.shipment_status_code, s.department,
        s.total_sales_amount, s.total_purchase_amount, s.total_gpm_amount,
        s.total_pieces, s.customer_company_id,
        c.name AS klant_naam
    FROM sprinter3000.shipments s
    LEFT JOIN sprinter3000.companies c ON s.customer_company_id = c.company_id
    WHERE s.report_date >= '{s}' AND s.report_date <= '{e}'
    ORDER BY s.report_date DESC
    """, "sprinter_ship")

    df_ship_v = fetch(f"""
    SELECT COUNT(*) AS n, SUM(total_gpm_amount) AS marge
    FROM sprinter3000.shipments
    WHERE report_date >= '{ps}' AND report_date <= '{pe}'
    """, "sprinter_ship_v")

    df_modes = fetch(f"""
    SELECT shipment_mode, COUNT(*) AS n, AVG(total_gpm_amount) AS gem_gpm
    FROM sprinter3000.shipments
    WHERE report_date >= '{s}' AND report_date <= '{e}'
    GROUP BY shipment_mode ORDER BY n DESC
    """, "modes")

    return {
        "shipments": df_records(df_ship),
        "shipments_yoy_aggregate": df_records(df_ship_v),
        "shipment_modes": df_records(df_modes),
    }


def bundle_hubspot(p):
    s, e = p["start_iso"], p["end_iso"]
    ps, pe = p["prev_start_iso"], p["prev_end_iso"]
    wr_s, wr_e = p["winrate_start_iso"], p["winrate_end_iso"]
    wr_ps, wr_pe = p["winrate_prev_start_iso"], p["winrate_prev_end_iso"]

    df_winrate = fetch(sql_winrate_by_pipeline(wr_s, wr_e), "winrate")
    df_winrate_v = fetch(sql_winrate_by_pipeline(wr_ps, wr_pe), "winrate_v")
    df_winrate_val = fetch(sql_winrate_validation(), "winrate_val")

    winrate_pipelines = build_winrate_rows(df_winrate)
    winrate_pipelines_prior = build_winrate_rows(df_winrate_v)
    winrate_validation = build_winrate_rows(df_winrate_val)

    df_deals = fetch(f"""
        SELECT
            d.id, d.createdat, d.updatedat,
            d.dealstage, d.dealname, d.amount, d.closedate,
            d.pipeline, d.hs_is_closed_won, d.hs_is_closed_lost,
            ps.label AS stage_label,
            pl.label AS pipeline_label,
            ps.metadata__isclosed AS is_gesloten,
            ps.metadata__probability AS kans
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        LEFT JOIN hubspot_v2.deals_pipeline pl ON d.pipeline = pl.id
        WHERE d.closedate >= '{wr_s}' AND d.closedate <= '{wr_e}'
          AND (d.hs_is_closed_won = 'true' OR d.hs_is_closed_lost = 'true')
        ORDER BY d.closedate DESC
    """, "deals")

    df_deals_v = fetch(f"""
        SELECT COUNT(*) AS n,
               SUM(CASE WHEN d.hs_is_closed_won = 'true' THEN 1 ELSE 0 END) AS won,
               SUM(CASE WHEN d.hs_is_closed_lost = 'true' THEN 1 ELSE 0 END) AS lost
        FROM hubspot_v2.deals d
        WHERE d.closedate >= '{wr_ps}' AND d.closedate <= '{wr_pe}'
          AND (d.hs_is_closed_won = 'true' OR d.hs_is_closed_lost = 'true')
    """, "deals_v")

    df_icp = fetch(f"""
        SELECT DATE_TRUNC('week', createdat) AS week, COUNT(*) AS deals
        FROM hubspot_v2.deals
        WHERE createdat >= '{s}' AND createdat <= '{e}'
        GROUP BY week ORDER BY week
    """, "icp_proxy")

    df_churn = fetch(f"""
        SELECT d.id, d.createdat, d.dealname, ps.label AS stage_label
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.createdat >= '{s}' AND d.createdat <= '{e}'
          AND ps.metadata__isclosed = 'true'
          AND (CAST(COALESCE(d.amount,'0') AS FLOAT) = 0
               OR LOWER(ps.label) LIKE '%lost%' OR LOWER(ps.label) LIKE '%verloren%')
        ORDER BY d.createdat DESC
    """, "churn")

    df_onb = fetch(f"""
        SELECT d.id, d.createdat, d.closedate, d.dealname, ps.label AS stage_label
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.closedate >= '{s}' AND d.closedate <= '{e}'
          AND ps.metadata__isclosed = 'true'
          AND CAST(COALESCE(d.amount,'0') AS FLOAT) > 0
    """, "onboarding")

    df_stages = fetch(
        "SELECT id, label, metadata__isclosed, metadata__probability "
        "FROM hubspot_v2.deals_pipeline__stages ORDER BY displayorder",
        "stages",
    )

    df_tick = fetch(f"""
        SELECT
            t.id, t.createdat, t.closed_date, t.subject,
            t.hs_ticket_priority, t.hs_pipeline, t.hs_pipeline_stage,
            t.category_issue, t.time_to_close, t.time_to_first_agent_reply,
            ps.label AS status_label
        FROM hubspot_v2.tickets t
        LEFT JOIN hubspot_v2.tickets_pipeline__stages ps ON t.hs_pipeline_stage = ps.id
        WHERE t.createdat >= '{s}' AND t.createdat <= '{e}'
        ORDER BY t.createdat DESC
    """, "tickets")

    df_tick_v = fetch(f"""
        SELECT COUNT(*) AS n FROM hubspot_v2.tickets
        WHERE createdat >= '{ps}' AND createdat <= '{pe}'
    """, "tickets_v")

    df_nps = fetch(f"""
        SELECT id, createdat, archived
        FROM hubspot_v2.feedback_submissions
        WHERE createdat >= '{s}' AND createdat <= '{e}'
        ORDER BY createdat DESC LIMIT 100
    """, "nps")

    return {
        "winrate_by_pipeline": winrate_pipelines,
        "winrate_by_pipeline_prior": winrate_pipelines_prior,
        "winrate_validation_full_history": winrate_validation,
        "winrate_period_label": p["winrate_period_label"],
        "deals": df_records(df_deals),
        "deals_yoy_counts": df_records(df_deals_v),
        "deals_per_week_proxy": df_records(df_icp),
        "churn_deals_proxy": df_records(df_churn),
        "onboarding_proxy": df_records(df_onb),
        "pipeline_stages": df_records(df_stages),
        "tickets": df_records(df_tick),
        "tickets_yoy_count": df_records(df_tick_v),
        "feedback_submissions_sample": df_records(df_nps),
    }


def resolve_bundle(q):
    b = str(q.get("bundle", "all")).lower().strip()
    if b not in ("cashweb", "hubspot", "sprinter", "all"):
        b = "all"
    return b


def handler(request):
    q = parse_query(request)
    bundle = resolve_bundle(q)
    p = build_params(q)

    out = {
        "bundle": bundle,
        "filters": {
            "book_year": p["book_year"],
            "month_filter": p["maanden_filter"],
            "book_periods": p["bp_str"],
            "book_periods_prior": p["bp_v_str"],
            "comparison_mode": p["comparison_mode"],
            "period_label": p["period_label"],
            "yoy_label": p["yoy_label"],
            "start_date": p["start_iso"],
            "end_date": p["end_iso"],
            "yoy_compare_window": {"start": p["prev_start_iso"], "end": p["prev_end_iso"]},
            "quarter": p["quarter"],
            "winrate_period_label": p["winrate_period_label"],
            "winrate_window": {
                "start": p["winrate_start_iso"],
                "end": p["winrate_end_iso"],
            },
        },
        "meta": {"warehouse": WAREHOUSE_DW},
    }

    if bundle == "cashweb":
        out["data"] = bundle_cashweb(p)
    elif bundle == "hubspot":
        out["data"] = bundle_hubspot(p)
    elif bundle == "sprinter":
        out["data"] = bundle_sprinter(p)
    else:
        out["data"] = {
            "cashweb": bundle_cashweb(p),
            "hubspot": bundle_hubspot(p),
            "sprinter": bundle_sprinter(p),
        }
    return out
