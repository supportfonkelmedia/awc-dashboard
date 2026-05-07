# MT Dashboard — Peliqan API handler (reference)
# Mirrors logic from documentation/PELIQAN_MT_DASHBOARD.md (Streamlit).
#
# Peliqan: App type "API endpoint handler", link GET route (e.g. /mt/data).
# Query params:
#   bundle   = cashweb | hubspot | sprinter | all   (default: all)
#   book_year = e.g. 2026                         (default: current calendar year)
#   month    = 1-12 | all                         (default: all = whole year in Cashweb filter)
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
CW_OMZET_DAGBOEKEN = "('50', 'VERK')"

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


def build_params(q):
    book_year = str(q.get("book_year") or datetime.today().year)
    month_raw = (q.get("month") or "all")
    mlow = str(month_raw).lower().strip()
    if mlow in ("", "all", "*"):
        maanden_filter = list(range(1, 13))
    else:
        maanden_filter = [int(month_raw)]

    _yy = int(str(book_year)[-2:])
    book_periods = [_yy * 100 + m for m in maanden_filter]
    bp_str = ", ".join(str(p) for p in book_periods)
    _yy_v = _yy - 1
    book_periods_v = [_yy_v * 100 + m for m in maanden_filter]
    bp_v_str = ", ".join(str(p) for p in book_periods_v)
    boekjaar_v = str(int(book_year) - 1)
    laatste_m = maanden_filter[-1]

    start_s = q.get("start_date")
    end_s = q.get("end_date")
    if start_s:
        start_date = datetime.strptime(str(start_s)[:10], "%Y-%m-%d").date()
    else:
        start_date = date(int(book_year), 1, 1)
    if end_s:
        end_date = datetime.strptime(str(end_s)[:10], "%Y-%m-%d").date()
    else:
        end_date = date.today()

    y_prev = int(book_year) - 1
    d0_prev = date(y_prev, maanden_filter[0], 1)
    d1_prev = month_end(y_prev, laatste_m)

    cw_f = cw_periode_filter(book_year, bp_str)
    cw_f_v = cw_periode_filter(boekjaar_v, bp_v_str)

    return {
        "book_year": book_year,
        "boekjaar_v": boekjaar_v,
        "maanden_filter": maanden_filter,
        "bp_str": bp_str,
        "bp_v_str": bp_v_str,
        "laatste_m": laatste_m,
        "start_date": start_date,
        "end_date": end_date,
        "start_iso": start_date.isoformat(),
        "end_iso": end_date.isoformat(),
        "prev_start_iso": d0_prev.isoformat(),
        "prev_end_iso": d1_prev.isoformat(),
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

    df_deals = fetch(f"""
        SELECT
            d.id, d.createdat, d.updatedat,
            d.dealstage, d.dealname, d.amount, d.closedate,
            ps.label AS stage_label,
            ps.metadata__isclosed AS is_gesloten,
            ps.metadata__probability AS kans
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.createdat >= '{s}' AND d.createdat <= '{e}'
        ORDER BY d.createdat DESC
    """, "deals")

    df_deals_v = fetch(f"""
        SELECT COUNT(*) AS n,
               SUM(CASE WHEN ps.metadata__isclosed='true'
                         AND CAST(COALESCE(d.amount,'0') AS FLOAT)>0 THEN 1 ELSE 0 END) AS won
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.createdat >= '{ps}' AND d.createdat <= '{pe}'
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
            "start_date": p["start_iso"],
            "end_date": p["end_iso"],
            "yoy_compare_window": {"start": p["prev_start_iso"], "end": p["prev_end_iso"]},
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
