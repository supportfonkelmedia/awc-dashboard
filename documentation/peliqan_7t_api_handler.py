# 7T WMS — Peliqan API handler (direct SQL Server, no Trino)
#
# Use in Peliqan:
#   1. Build → Apps → add script → type "API endpoint handler".
#   2. Replace the editor content with this file.
#   3. Build → API endpoints → add route, Method GET, attach this app, JWT on.
#   4. Suggested route: /awc/7t  →  Laravel calls:
#        GET https://api.eu.peliqan.io/{your_id}/awc/7t?wms_part=all
#        Authorization: JWT {token}
#
# Query parameters:
#   wms_part = occupancy,leadtime,accuracy,ontvangsten | all   (default: all)
#
# Why this exists:
#   Trino over 7T is slow and unreliable. This handler talks straight to the 7T
#   SQL Server via pq.dbconnect("7T") and runs server-side aggregates only — no
#   full table transfers, no Trino fallback, no dual-dialect SQL. The AWC handler
#   (peliqan_awc_api_handler.py) now only serves HubSpot/finance from dw_2401.
#
# Returns {bundle, meta, data} so the existing Vue WMS composables keep working:
#   data = the WMS KPI summary (occupancy / storage_lead_time_days /
#          inventory_accuracy_pct / ontvangsten_count / errors).

import json
import re
import time
from urllib.parse import parse_qs

import pandas as pd

# --- Connection ids: must match the Peliqan 7T database / connection exactly. ---
CONNECT_7T = "7T"
FETCH_DB_7T = "DB7T"
SCHEMA_DBO = "dbo"

# AWC administratie selector. The 7T Administraties table identifies AWC by
# Naam = 'AWC' (ID 1); there is no usable 'alaw' code column here.
AWC_ADMIN_CODE = "AWC"
AWC_ADMIN_COLUMN = "Naam"

# Shorter lookback + SQL aggregates keep the WMS summary fast.
WMS_LOOKBACK_DAYS = 180
# Hard ceiling for the ?lookback= override (debug sweeps), so we never ask for an
# unbounded scan that trips Peliqan's execution limit.
WMS_LOOKBACK_MAX = 3650
# Bump on redeploy — surfaces in API meta to confirm Peliqan has the latest script.
HANDLER_VERSION = "2026-09-10-7t-dock-to-stock-v2"

# pq.dbconnect("7T") is the warehouse connection id — not a valid conn.fetch() database name.
FETCH_DB_CANDIDATES = (FETCH_DB_7T, "db_7t", "db7t")

# --- Lazy connection state (import-time dbconnect can 500 the endpoint) ---
_dbconn_7t = None
_7T_FETCH_DB = None
_7T_AVAILABLE = False
_7T_PROBE_ERROR = None
_7T_LAST_ERROR = None
_AWC_ADMIN_ID = None
# Per-request lookback window (overridable via ?lookback=); reset each request.
_ACTIVE_LOOKBACK = WMS_LOOKBACK_DAYS
# Dock-to-Stock calendar year (overridable via ?year=); reset each request.
_ACTIVE_DOCK_YEAR = None


def _get_7t_conn():
    global _dbconn_7t
    if _dbconn_7t is None:
        _dbconn_7t = pq.dbconnect(CONNECT_7T)
    return _dbconn_7t


def _reset_state():
    global _dbconn_7t, _7T_FETCH_DB, _7T_AVAILABLE, _7T_PROBE_ERROR
    global _7T_LAST_ERROR, _AWC_ADMIN_ID, _ACTIVE_LOOKBACK, _ACTIVE_DOCK_YEAR
    _dbconn_7t = None
    _7T_FETCH_DB = None
    _7T_AVAILABLE = False
    _7T_PROBE_ERROR = None
    _7T_LAST_ERROR = None
    _AWC_ADMIN_ID = None
    _ACTIVE_LOOKBACK = WMS_LOOKBACK_DAYS
    _ACTIVE_DOCK_YEAR = None


def _apply_lookback(request):
    """Override the lookback window from ?lookback=DAYS (clamped). Returns the value."""
    global _ACTIVE_LOOKBACK
    raw = _query_param(request, "lookback", None)
    if raw is not None:
        try:
            days = int(str(raw).strip())
            if days > 0:
                _ACTIVE_LOOKBACK = min(days, WMS_LOOKBACK_MAX)
        except (TypeError, ValueError):
            pass
    return _ACTIVE_LOOKBACK


def _apply_dock_year(request):
    """Calendar year for Dock-to-Stock (?year=). Defaults to current UTC year."""
    global _ACTIVE_DOCK_YEAR
    raw = _query_param(request, "year", None)
    year = None
    if raw is not None:
        try:
            year = int(str(raw).strip())
        except (TypeError, ValueError):
            year = None
    if year is None or year < 2000 or year > 2100:
        year = pd.Timestamp.utcnow().year
    _ACTIVE_DOCK_YEAR = year
    return _ACTIVE_DOCK_YEAR


def _short_err(exc):
    msg = str(exc)
    m = re.search(r"message='([^']+)'", msg) or re.search(r'message="([^"]+)"', msg)
    if m:
        return m.group(1)
    m = re.search(r"PeliqanClientException\('([^']+)'", msg)
    if m:
        return m.group(1)
    return f"{type(exc).__name__}: {msg[:240]}"


def _fetch_db_keys():
    """Database names for conn.fetch() — never use CONNECT_7T (that is dbconnect id only)."""
    keys = []
    cached = str(_7T_FETCH_DB or "").strip()
    if cached and cached.upper() != CONNECT_7T.upper():
        keys.append(cached)
    for key in FETCH_DB_CANDIDATES:
        key = str(key or "").strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def query_7t(sql):
    """Run a query against the 7T SQL Server (direct, df=True). Returns (df, err)."""
    global _7T_LAST_ERROR, _7T_FETCH_DB
    fetch_keys = _fetch_db_keys()
    last_err = None
    try:
        conn = _get_7t_conn()
        for fetch_key in fetch_keys:
            try:
                df = conn.fetch(fetch_key, query=sql, df=True)
                if df is None:
                    last_err = f"{fetch_key}: empty result"
                    continue
                _7T_FETCH_DB = fetch_key
                _7T_LAST_ERROR = None
                return df, None
            except Exception as e:
                last_err = _short_err(e)
        err = last_err or "7T query returned no data"
        _7T_LAST_ERROR = err
        return pd.DataFrame(), err
    except Exception as e:
        err = _short_err(e)
        _7T_LAST_ERROR = err
        return pd.DataFrame(), err


def _scalar(df, col, default=None):
    if df is None or df.empty or col not in df.columns:
        return default
    val = df.iloc[0][col]
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    return val


def _col(df, name):
    if df is None or df.empty:
        return None
    lookup = {str(c).lower(): c for c in df.columns}
    return lookup.get(str(name).lower())


def _ping_7t():
    """
    Probe connectivity AND resolve the AWC administratie id in one round trip.

    Availability is connection-based (no SQL error), not row-based: if the AWC
    administratie is missing we still report available=True so the empty result is
    distinguishable from a broken connection. probe_rows tells you whether the
    AWC administratie was actually found.
    """
    global _7T_AVAILABLE, _7T_PROBE_ERROR, _AWC_ADMIN_ID
    code = str(AWC_ADMIN_CODE).replace("'", "''")
    df, err = query_7t(
        f"SELECT TOP 1 ID AS admin_id FROM dbo.Administraties "
        f"WHERE {AWC_ADMIN_COLUMN} = '{code}'"
    )
    _7T_PROBE_ERROR = err
    _7T_AVAILABLE = err is None
    if err is None and df is not None and not df.empty:
        col = _col(df, "admin_id") or _col(df, "ID")
        if col is not None:
            val = df.iloc[0][col]
            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                _AWC_ADMIN_ID = int(val)
    return df, err


def _resolve_awc_admin_id(adm_df=None):
    """Return the AWC administratie id resolved during _ping_7t (or None)."""
    return _AWC_ADMIN_ID


def _awc_admin_filter(table_admin_col="Administratie_ID", table_alias="mag"):
    if _AWC_ADMIN_ID is not None:
        return f"{table_alias}.{table_admin_col} = {_AWC_ADMIN_ID}"
    code = str(AWC_ADMIN_CODE).replace("'", "''")
    return (
        f"EXISTS (SELECT 1 FROM dbo.Administraties adm "
        f"WHERE adm.ID = {table_alias}.{table_admin_col} "
        f"AND adm.{AWC_ADMIN_COLUMN} = '{code}')"
    )


def _lookback(column, alias=None):
    prefix = f"{alias}." if alias else ""
    return f"{prefix}{column} >= DATEADD(day, -{_ACTIVE_LOOKBACK}, CAST(GETDATE() AS DATE))"


def load_kpis_combined():
    """
    All four WMS KPIs in a single round trip via scalar subqueries.

    The 7T connection has high per-fetch overhead (~12s/call), so one query for
    everything is far faster than four. Trade-off: any SQL error fails the whole
    batch rather than one metric.
    """
    adm_mag = _awc_admin_filter(table_alias="mag")
    adm_ord = _awc_admin_filter(table_admin_col="Administratie_ID", table_alias="ord")
    # Ontvangsten.Administratie_ID is unpopulated (always NULL) in this DB7T
    # instance, which is AWC's own WMS — so receipts are scoped by date only.
    # Telling_Locaties.Datum_Telling_Gereed is also NULL, so accuracy can't use a
    # date window; it runs over all completed counts for AWC warehouses.
    tsql = f"""
        SELECT
            (SELECT COUNT(*)
                FROM dbo.Magazijn_Plaatscodes mpc
                INNER JOIN dbo.Magazijnen mag ON mpc.Magazijn_ID = mag.ID
                WHERE mpc.Extern = 0
                  AND mpc.Geblokkeerd_Voor_Picken = 0
                  AND {adm_mag}) AS occ_total,
            (SELECT COUNT(*)
                FROM dbo.Magazijn_Plaatscodes mpc
                INNER JOIN dbo.Magazijnen mag ON mpc.Magazijn_ID = mag.ID
                WHERE mpc.Extern = 0
                  AND mpc.Geblokkeerd_Voor_Picken = 0
                  AND {adm_mag}
                  AND EXISTS (
                      SELECT 1 FROM dbo.Artikel_Magazijnlocaties aml
                      WHERE aml.Magazijn_Plts_ID = mpc.ID
                        AND aml.Technische_Voorraad > 0
                        AND aml.Er_Is_Voorraad = 1)) AS occ_occupied,
            (SELECT AVG(CAST(DATEDIFF(day, ld.Oude_Leverdatum, ld.Nieuwe_Leverdatum) AS FLOAT))
                FROM dbo.Orderregel_Leverdata ld
                INNER JOIN dbo.Orderregels orr ON ld.Orderregel_ID = orr.ID
                INNER JOIN dbo.Orders ord ON orr.Order_ID = ord.ID
                WHERE ld.Informatief = 0
                  AND {adm_ord}
                  AND {_lookback("AanmaakDatum", "ld")}
                  AND ld.Oude_Leverdatum IS NOT NULL
                  AND ld.Nieuwe_Leverdatum IS NOT NULL
                  AND ld.Nieuwe_Leverdatum >= ld.Oude_Leverdatum) AS lead_days,
            (SELECT SUM(CASE WHEN tl.Totaal_Aantal_Verwacht = tl.Totaal_Aantal_Geteld THEN 1 ELSE 0 END)
                FROM dbo.Telling_Locaties tl
                INNER JOIN dbo.Tellingen t ON tl.Telling_ID = t.ID
                INNER JOIN dbo.Magazijnen mag ON t.Magazijn_ID = mag.ID
                WHERE tl.Telling_Gereed = 1
                  AND {adm_mag}
                  AND (tl.Totaal_Aantal_Verwacht > 0 OR tl.Totaal_Aantal_Geteld > 0)) AS acc_matched,
            (SELECT COUNT(*)
                FROM dbo.Telling_Locaties tl
                INNER JOIN dbo.Tellingen t ON tl.Telling_ID = t.ID
                INNER JOIN dbo.Magazijnen mag ON t.Magazijn_ID = mag.ID
                WHERE tl.Telling_Gereed = 1
                  AND {adm_mag}
                  AND (tl.Totaal_Aantal_Verwacht > 0 OR tl.Totaal_Aantal_Geteld > 0)) AS acc_total,
            (SELECT COUNT(*)
                FROM dbo.Ontvangsten o
                WHERE {_lookback("Datum", "o")}) AS ontv_count
    """
    df, err = query_7t(tsql)
    if err:
        return None, err

    occ_total = int(_scalar(df, "occ_total", 0) or 0)
    occ_occupied = int(_scalar(df, "occ_occupied", 0) or 0)
    occ_rate = round((occ_occupied / occ_total) * 1000) / 10 if occ_total else None

    lead_raw = _scalar(df, "lead_days")
    lead_days = round(float(lead_raw) * 10) / 10 if lead_raw is not None else None

    acc_total = int(_scalar(df, "acc_total", 0) or 0)
    acc_matched = int(_scalar(df, "acc_matched", 0) or 0)
    accuracy = round((acc_matched / acc_total) * 1000) / 10 if acc_total else None

    ontv_count = int(_scalar(df, "ontv_count", 0) or 0)

    return {
        "occupancy": {"total": occ_total, "occupied": occ_occupied, "rate": occ_rate},
        "storage_lead_time_days": lead_days,
        "inventory_accuracy_pct": accuracy,
        "ontvangsten_count": ontv_count,
    }, None


def _median(values):
    nums = [float(v) for v in values if v is not None and not pd.isna(v)]
    if not nums:
        return None
    nums.sort()
    n = len(nums)
    mid = n // 2
    if n % 2:
        return nums[mid]
    return (nums[mid - 1] + nums[mid]) / 2.0


def _dock_measured_subquery(start, end):
    """Shared measured-order subquery (Brief Fonkel deel 3 validatiequery)."""
    return f"""
        SELECT
            LTRIM(RTRIM(s.ID)) AS sid,
            s.Los_Datum AS los,
            MIN(vv.MutatieDatum) AS klaar
        FROM dbo.Spare_Orders s
        INNER JOIN dbo.Ontvangsten o
            ON LTRIM(RTRIM(o.Spare_Order_ID)) = LTRIM(RTRIM(s.ID))
        INNER JOIN dbo.Voorraad_Verplaatsingen vv
            ON vv.Ontvangst_ID = o.ID AND vv.Status = 30
        WHERE s.Los_Datum >= '{start}'
          AND s.Los_Datum < '{end}'
          AND s.Gelost = 1
        GROUP BY LTRIM(RTRIM(s.ID)), s.Los_Datum
    """


def load_dock_to_stock(year):
    """
    Brief Fonkel deel 3: Dock-to-Stock (% binnen 24u na lossen).

    Per inbound (Spare_Orders, Gelost=1): Los_Datum → eerste Voorraad_Verplaatsingen
    met Status=30 (MutatieDatum). KPI alleen over orders mét status-30-verplaatsing;
    dekking = meetbaar / alle geloste orders in het jaar.
    """
    y = int(year)
    start = f"{y}-01-01"
    end = f"{y + 1}-01-01"
    measured = _dock_measured_subquery(start, end)

    summary_sql = f"""
        SELECT
            (SELECT COUNT(*)
                FROM dbo.Spare_Orders s
                WHERE s.Los_Datum >= '{start}'
                  AND s.Los_Datum < '{end}'
                  AND s.Gelost = 1) AS total_unloaded,
            COUNT(*) AS measurable_orders,
            SUM(CASE WHEN DATEDIFF(hour, x.los, x.klaar) <= 24 THEN 1 ELSE 0 END) AS within_24h,
            CAST(
                100.0 * SUM(CASE WHEN DATEDIFF(hour, x.los, x.klaar) <= 24 THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0) AS numeric(5, 1)
            ) AS pct_within_24h
        FROM ({measured}) x
    """

    monthly_sql = f"""
        SELECT
            MONTH(x.los) AS month,
            COUNT(*) AS orders,
            SUM(CASE WHEN DATEDIFF(hour, x.los, x.klaar) <= 24 THEN 1 ELSE 0 END) AS within_24h,
            CAST(
                100.0 * SUM(CASE WHEN DATEDIFF(hour, x.los, x.klaar) <= 24 THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0) AS numeric(5, 1)
            ) AS pct_within_24h
        FROM ({measured}) x
        GROUP BY MONTH(x.los)
        ORDER BY MONTH(x.los)
    """

    df_sum, err_sum = query_7t(summary_sql)
    if err_sum:
        return None, err_sum

    df_mon, err_mon = query_7t(monthly_sql)
    if err_mon:
        return None, err_mon

    total_unloaded = int(_scalar(df_sum, "total_unloaded", 0) or 0)
    measurable = int(_scalar(df_sum, "measurable_orders", 0) or 0)
    within_24h = int(_scalar(df_sum, "within_24h", 0) or 0)
    pct = _scalar(df_sum, "pct_within_24h")

    median_hours = None
    if measurable > 0:
        hours_sql = f"""
            SELECT DATEDIFF(hour, x.los, x.klaar) AS hours
            FROM ({measured}) x
        """
        df_hours, err_hours = query_7t(hours_sql)
        if err_hours:
            return None, err_hours
        if df_hours is not None and not df_hours.empty:
            col = _col(df_hours, "hours") or "hours"
            med = _median(df_hours[col].tolist())
            median_hours = round(float(med), 1) if med is not None else None

    coverage_pct = (
        round((measurable / total_unloaded) * 1000) / 10
        if total_unloaded
        else None
    )

    monthly = []
    if df_mon is not None and not df_mon.empty:
        for _, row in df_mon.iterrows():
            mo = int(row.get("month") or row.get("MONTH") or 0)
            orders = int(row.get("orders") or 0)
            w24 = int(row.get("within_24h") or 0)
            pct_m = row.get("pct_within_24h")
            monthly.append(
                {
                    "month": mo,
                    "year": y,
                    "orders": orders,
                    "within_24h": w24,
                    "pct_within_24h": float(pct_m) if pct_m is not None else None,
                }
            )

    return {
        "year": y,
        "total_unloaded": total_unloaded,
        "measurable_orders": measurable,
        "within_24h": within_24h,
        "pct_within_24h": float(pct) if pct is not None else None,
        "median_hours": median_hours,
        "coverage_pct": coverage_pct,
        "monthly": monthly,
        "norm_hours": 24,
    }, None


def _resolve_wms_parts(request):
    raw = str(_query_param(request, "wms_part", "all") or "all").lower().strip()
    allowed = {"occupancy", "leadtime", "accuracy", "ontvangsten"}
    if raw in ("", "all", "*"):
        return set(allowed)
    parts = {p.strip() for p in raw.split(",") if p.strip() in allowed}
    return parts or set(allowed)


def build_wms_summary(request=None):
    _reset_state()
    lookback = _apply_lookback(request)
    dock_year = _apply_dock_year(request)
    parts = _resolve_wms_parts(request)
    query_stats = {}

    t0 = time.time()
    adm_df, probe_err = _ping_7t()
    query_stats["probe_ms"] = int((time.time() - t0) * 1000)

    admin_id = _resolve_awc_admin_id(adm_df)

    if not _7T_AVAILABLE:
        return {
            "wms_available": False,
            "format": "summary",
            "summary_source": "direct_sql",
            "handler_version": HANDLER_VERSION,
            "lookback_days": lookback,
            "admin_column": AWC_ADMIN_COLUMN,
            "admin_id": admin_id,
            "probe_error": probe_err,
            "probe_rows": int(len(adm_df)),
            "wms_parts": sorted(parts),
            "query_stats": query_stats,
        }

    occupancy = {"total": 0, "occupied": 0, "rate": None}
    lead_days = accuracy = None
    ontv_count = 0
    dock_to_stock = None
    errors = None

    # Single round trip: all KPIs computed regardless of ?wms_part= (it stays in
    # the response for visibility but no longer drives separate queries).
    t0 = time.time()
    kpis, err = load_kpis_combined()
    query_stats["kpis_ms"] = int((time.time() - t0) * 1000)
    if err:
        errors = {"kpis": err}
    elif kpis:
        occupancy = kpis["occupancy"]
        lead_days = kpis["storage_lead_time_days"]
        accuracy = kpis["inventory_accuracy_pct"]
        ontv_count = kpis["ontvangsten_count"]

    t0 = time.time()
    d2s, d2s_err = load_dock_to_stock(dock_year)
    query_stats["dock_to_stock_ms"] = int((time.time() - t0) * 1000)
    if d2s_err:
        errors = {**(errors or {}), "dock_to_stock": d2s_err}
    elif d2s:
        dock_to_stock = d2s

    return {
        "wms_available": True,
        "format": "summary",
        "summary_source": "aggregate_sql",
        "handler_version": HANDLER_VERSION,
        "lookback_days": lookback,
        "dock_to_stock_year": dock_year,
        "admin_column": AWC_ADMIN_COLUMN,
        "admin_id": admin_id,
        "probe_rows": int(len(adm_df)),
        "wms_parts": sorted(parts),
        "query_stats": query_stats,
        "occupancy": occupancy,
        "storage_lead_time_days": lead_days,
        "inventory_accuracy_pct": accuracy,
        "ontvangsten_count": ontv_count,
        "dock_to_stock": dock_to_stock,
        "errors": errors,
    }


def _parsed_query(request):
    out = {}
    try:
        if request is None:
            return out
        if isinstance(request, dict):
            for key in ("query", "query_params", "queryStringParameters"):
                raw = request.get(key)
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        if isinstance(v, (list, tuple)) and v:
                            out[k] = v[0]
                        elif v is not None:
                            out[k] = v
            qs = (
                request.get("query_string")
                or request.get("queryString")
                or request.get("raw_query_string")
            )
            if isinstance(qs, str) and qs.strip():
                for k, v in parse_qs(qs.lstrip("?")).items():
                    if v:
                        out[k] = v[0]
            url = request.get("url") or request.get("path", "")
            if isinstance(url, str) and "?" in url:
                for k, v in parse_qs(url.split("?", 1)[1]).items():
                    if v:
                        out[k] = v[0]
        else:
            if hasattr(request, "args"):
                for k, v in dict(request.args).items():
                    out[k] = v
            elif hasattr(request, "query_params"):
                qp = request.query_params
                if hasattr(qp, "items"):
                    for k, v in qp.items():
                        out[k] = v
    except Exception:
        pass
    return out


def _query_param(request, key, default=None):
    val = _parsed_query(request).get(key)
    return default if val is None else val


def _records(df):
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def build_sample(request=None):
    """
    Cheap direct-SQL probe (no Trino, no FOR JSON): the 10 most-recent rows from
    each problem table in one round trip, normalized to a shared shape so we can
    see the real Administratie_ID / Magazijn_ID / flags driving the empty KPIs.

    Columns per row:
      tbl      = source table
      id       = ID
      admin_id = Administratie_ID (Ontvangsten/Orders) else NULL
      ref      = Relatie_ID / Orderregel_ID / Magazijn_ID / Telling_ID
      flag     = Ontvangst_Definitief / Informatief / Telling_Gereed
      dt       = relevant date
    Trigger with ?sample=1.
    """
    _reset_state()
    adm_df, probe_err = _ping_7t()
    admin_id = _resolve_awc_admin_id(adm_df)
    if not _7T_AVAILABLE:
        return {"sample": True, "admin_id": admin_id, "probe_error": probe_err}

    sql = """
        SELECT * FROM (
            SELECT TOP 10 'Ontvangsten' AS tbl, CAST(o.ID AS bigint) AS id,
                CAST(o.Administratie_ID AS bigint) AS admin_id,
                CAST(o.Relatie_ID AS bigint) AS ref,
                CAST(o.Ontvangst_Definitief AS int) AS flag,
                CONVERT(varchar(19), o.Datum, 120) AS dt
            FROM dbo.Ontvangsten o ORDER BY o.ID DESC
        ) a
        UNION ALL
        SELECT * FROM (
            SELECT TOP 10 'Orders' AS tbl, CAST(ord.ID AS bigint) AS id,
                CAST(ord.Administratie_ID AS bigint) AS admin_id,
                CAST(NULL AS bigint) AS ref,
                CAST(NULL AS int) AS flag,
                CAST(NULL AS varchar(19)) AS dt
            FROM dbo.Orders ord ORDER BY ord.ID DESC
        ) b
        UNION ALL
        SELECT * FROM (
            SELECT TOP 10 'Tellingen' AS tbl, CAST(t.ID AS bigint) AS id,
                CAST(NULL AS bigint) AS admin_id,
                CAST(t.Magazijn_ID AS bigint) AS ref,
                CAST(NULL AS int) AS flag,
                CAST(NULL AS varchar(19)) AS dt
            FROM dbo.Tellingen t ORDER BY t.ID DESC
        ) d
        UNION ALL
        SELECT * FROM (
            SELECT TOP 10 'Telling_Locaties' AS tbl, CAST(tl.ID AS bigint) AS id,
                CAST(NULL AS bigint) AS admin_id,
                CAST(tl.Telling_ID AS bigint) AS ref,
                CAST(tl.Telling_Gereed AS int) AS flag,
                CONVERT(varchar(19), tl.Datum_Telling_Gereed, 120) AS dt
            FROM dbo.Telling_Locaties tl ORDER BY tl.ID DESC
        ) e
    """
    df, err = query_7t(sql)
    if err:
        return {"sample": True, "admin_id": admin_id, "error": err}
    return {"sample": True, "admin_id": admin_id, "rows": _records(df)}


def build_payload(request=None):
    if str(_query_param(request, "sample", "") or "").lower().strip() in ("1", "true", "yes"):
        return {
            "bundle": "wms",
            "meta": {"handler_version": HANDLER_VERSION, "sample": True},
            "data": build_sample(request=request),
        }
    wms = build_wms_summary(request=request)
    meta = {
        "handler_version": HANDLER_VERSION,
        "source": "7t_direct_sql",
        "warehouses": {
            "wms_connect": CONNECT_7T,
            "wms_db": _7T_FETCH_DB or FETCH_DB_7T,
            "wms_mode": "direct_sql",
        },
        "wms": {
            "available": bool(wms.get("wms_available")),
            "probe_error": wms.get("probe_error") or _7T_PROBE_ERROR,
            "probe_rows": wms.get("probe_rows"),
            "handler_version": wms.get("handler_version", HANDLER_VERSION),
            "admin_id": wms.get("admin_id"),
            "summary_source": wms.get("summary_source"),
            "format": wms.get("format", "summary"),
            "lookback_days": wms.get("lookback_days", WMS_LOOKBACK_DAYS),
        },
    }
    return {"bundle": "wms", "meta": meta, "data": wms}


def handler(request):
    """Required entrypoint for Peliqan published API endpoints."""
    try:
        return build_payload(request=request)
    except Exception as e:
        return {
            "status": "error",
            "message": f"{type(e).__name__}: {e}",
            "bundle": "wms",
            "meta": {
                "wms": {
                    "probe_error": _7T_PROBE_ERROR,
                    "last_sql_error": _7T_LAST_ERROR,
                }
            },
        }
