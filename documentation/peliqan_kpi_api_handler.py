# KPI MT-dashboard — Peliqan API handler (Overdracht Fonkel)
#
# Deploy in Peliqan:
#   1. Build → Apps → API endpoint handler → paste this script.
#   2. API route GET e.g. /kpi/data  (JWT on).
#   3. Laravel: PELIQAN_KPI_DATA_URL=https://api.eu.peliqan.io/{id}/kpi/data
#
# Query params:
#   bundle = screen | controles | drill | registry   (default: screen)
#   scherm = strategisch | operationeel | tactisch | awc | afc | acc  (required for screen)
#   views  = comma-separated drill view base names (for drill), e.g. kpi_bm_maand,kpi_ebitda_maand
#   limit  = max rows per drill view (default 2000, max 5000)
#   scope       = optional drill filter on scope_code / scope (only views that have that column)
#   periode_van = optional drill filter YYYY, YYYY-MM or YYYY-MM-DD on the view's period column
#
# Drill (v7; v10 adds scope via admin_code/pipeline and the kpi_churn_klant / kpi_winrate_deal views): rows are ordered in SQL (period column DESC where the view has one, else a stable key,
# with the full row text as final tie-breaker) and LIMIT is applied in SQL after ordering.
# Additive response key `table_meta` per view: row_count, truncated, total_count, limit, order_by, filters.
# Existing keys (bundle, views, tables, errors, meta) are unchanged; truncation still also adds the
# old {view, warning: truncated_to_N_rows} entry to errors[].
#
# Reads replicated KPI tables in warehouse dw_2401, schema "My Queries", suffix _my_queries.
# Fonkel/Laravel does tegel assembly & formatting; this handler only fetches rows.

import json
import os
import re
from urllib.parse import parse_qs, urlparse

import pandas as pd

WAREHOUSE_DW = "dw_2401"
KPI_SCHEMA = '"My Queries"'
HANDLER_VERSION = "2026-11-12-kpi-v10-drill-detail-scope"

SCREENS = frozenset(
    {"strategisch", "operationeel", "tactisch", "awc", "afc", "acc"}
)

# Drill views named in Overdracht (base name without _my_queries)
ALLOWED_DRILL_VIEWS = frozenset(
    {
        "kpi_bm_maand",
        "kpi_ebitda_maand",
        "kpi_kosten_maand",
        "kpi_omzetbrug",
        "kpi_omzetbrug_top",
        "kpi_omzetbrug_klant",
        "kpi_triple_lob_maand",
        "kpi_triple_lob_te_controleren",
        "kpi_winrate_maand",
        "kpi_winrate_fases",
        "kpi_churn_kwartaal",
        # v10: detail-drills onder Churn en Winrate (één rij per klant / deal)
        "kpi_churn_klant",
        "kpi_winrate_deal",
        "kpi_acc_dossiers_maand",
        "kpi_acc_doorlooptijd_maand",
        "kpi_onboarding_kwartaal",
        "kpi_d2s_maand",
        "kpi_awc_ops_maand",
        "kpi_awc_schade_klant",
        "kpi_afc_sprinter_maand",
        # AFC-analyse (/kpi/afc/analyse), zie documentation/AFC-analyse.md in awc-dashboard
        "kpi_afc_zending_maand",
        "kpi_afc_eigenaar_maand",
        "kpi_afc_klant_jaar",
        "kpi_afc_klant",
        "kpi_afc_klant_retentie_jaar",
        "kpi_afc_resultaat_maand",
        "kpi_afc_offerte_maand",
        "kpi_handmatig",
        "kpi_doelen",
        "kpi_intercompany",
        "kpi_controles",
        "kpi_registry",
        "kpi_tegel_config",
        "kpi_oordeel",
        "kpi_trend",
    }
)


# Drill ordering per view: (period column or None, ORDER BY expression). Column names checked
# against the _my_queries replicas on 2026-11-12. A final `t::text` tie-breaker is appended so the
# order (and therefore any truncated subset) is fully deterministic.
DRILL_ORDER = {
    "kpi_bm_maand": ("maand", "t.maand DESC, t.admin_code"),
    "kpi_ebitda_maand": ("maand", "t.maand DESC, t.scope_code"),
    "kpi_kosten_maand": ("maand", "t.maand DESC, t.scope_code, t.groep"),
    "kpi_omzetbrug": ("stand_per", "t.stand_per DESC, t.scope, t.volgorde"),
    "kpi_omzetbrug_top": ("stand_per", "t.stand_per DESC, t.scope, t.lijst, t.rang"),
    "kpi_omzetbrug_klant": ("stand_per", "t.stand_per DESC, t.scope, ABS(t.verschil) DESC NULLS LAST, t.klant"),
    "kpi_triple_lob_maand": ("maand", "t.maand DESC"),
    "kpi_triple_lob_te_controleren": (None, "t.omzet_12m DESC NULLS LAST, t.zoek"),
    "kpi_winrate_maand": ("peildatum", "t.peildatum DESC, t.pipeline, t.soort"),
    "kpi_winrate_fases": (None, "t.pipeline, t.fase"),
    "kpi_churn_kwartaal": ("kwartaal", "t.kwartaal DESC"),
    "kpi_churn_klant": ("vertrekdatum", "t.vertrekdatum DESC, t.klant"),
    "kpi_winrate_deal": (
        "aangemaakt",
        "CASE t.tegelvenster WHEN 'telt mee' THEN 0 WHEN 'nog open' THEN 1 ELSE 2 END, "
        "t.beslisdatum DESC NULLS LAST, t.aangemaakt DESC, t.deal",
    ),
    "kpi_acc_dossiers_maand": ("maand", "t.maand DESC, t.soort"),
    "kpi_acc_doorlooptijd_maand": ("maand", "t.maand DESC"),
    "kpi_onboarding_kwartaal": ("kwartaal", "t.kwartaal DESC, t.pijplijn"),
    "kpi_d2s_maand": ("maand", "t.maand DESC"),
    "kpi_awc_ops_maand": ("maand", "t.maand DESC"),
    "kpi_awc_schade_klant": (None, "t.rang, t.relatie_id"),
    "kpi_afc_sprinter_maand": ("maand", "t.maand DESC"),
    "kpi_afc_zending_maand": ("maand", "t.maand DESC, t.modaliteit, t.richting"),
    "kpi_afc_eigenaar_maand": ("maand", "t.maand DESC, t.eigenaar"),
    "kpi_afc_klant_jaar": (None, "t.jaar DESC, t.omzet DESC NULLS LAST, t.klantgroep_id"),
    "kpi_afc_klant": (None, "t.omzet_12m DESC NULLS LAST, t.klant_id"),
    "kpi_afc_klant_retentie_jaar": (None, "t.jaar"),
    "kpi_afc_resultaat_maand": ("maand", "t.maand DESC"),
    "kpi_afc_offerte_maand": ("maand", "t.maand DESC"),
    "kpi_handmatig": ("periode_einde", "t.periode_einde DESC, t.kpi_code, t.scope_code"),
    "kpi_doelen": ("geldig_vanaf", "t.geldig_vanaf DESC, t.kpi_code, t.scope_code"),
    "kpi_intercompany": (None, "t.admin_code, t.zoek"),
    "kpi_controles": (None, "t.volgorde, t.controle"),
    "kpi_registry": (None, "t.volgorde, t.kpi_code"),
    "kpi_tegel_config": (None, "t.scherm, t.positie"),
    "kpi_oordeel": (None, "t.volgorde, t.kpi_code, t.scope_code"),
    "kpi_trend": ("periode", "t.periode DESC, t.kpi_code, t.scope_code, t.serie, t.volgnummer"),
}

# Optional `scope` drill filter: views with a scope_code column, and the omzetbrug views whose
# `scope` column holds labels (Concern/AWC/AFC/ACC) instead of codes.
DRILL_SCOPE_CODE_VIEWS = frozenset(
    {"kpi_ebitda_maand", "kpi_kosten_maand", "kpi_handmatig", "kpi_doelen", "kpi_oordeel", "kpi_trend",
     "kpi_churn_klant", "kpi_winrate_deal"}
)
DRILL_SCOPE_LABEL_VIEWS = frozenset({"kpi_omzetbrug", "kpi_omzetbrug_top", "kpi_omzetbrug_klant"})
SCOPE_CODE_TO_LABEL = {"concern": "Concern", "alaw": "AWC", "pgl1": "AFC", "acco": "ACC"}
# v10: views whose scope sits in another column than scope_code (bm: admin_code, winrate: pipeline).
DRILL_SCOPE_OTHER_COLUMN = {
    "kpi_bm_maand": "admin_code",
    "kpi_winrate_maand": "pipeline",
    "kpi_winrate_fases": "pipeline",
}
# v10: views without concern rows (concern = sum of the entities): scope=concern means "all rows".
DRILL_CONCERN_IS_ALL = frozenset({"kpi_bm_maand", "kpi_kosten_maand"})

_dbconn = None


def _get_conn():
    global _dbconn
    if _dbconn is None:
        _dbconn = pq.dbconnect(WAREHOUSE_DW)
    return _dbconn


def df_records(df):
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def kpi_relation(base_name):
    """Map logical view name to quoted relation in My Queries."""
    name = base_name.strip()
    if not name.endswith("_my_queries"):
        name = f"{name}_my_queries"
    return f"{KPI_SCHEMA}.{name}"


def fetch(query, label="q"):
    try:
        df = _get_conn().fetch(WAREHOUSE_DW, query=query, df=True)
        return (df if df is not None else pd.DataFrame()), None
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def fetch_table(base_name):
    rel = kpi_relation(base_name)
    return fetch(f"SELECT * FROM {rel}", base_name)


def _is_nonempty_scalar(val):
    if val is None:
        return False
    if isinstance(val, str):
        return val.strip() != ""
    if isinstance(val, (list, tuple)):
        return any(_is_nonempty_scalar(x) for x in val)
    return True


def _last_nonempty_from_sequence(seq):
    """Prefer last non-empty element (parse_qs/getlist may end with '')."""
    if seq is None:
        return ""
    if not isinstance(seq, (list, tuple)):
        return seq
    for x in reversed(seq):
        if _is_nonempty_scalar(x):
            return x
    return seq[-1] if seq else ""


def _merge_query_dict(target, blob):
    """Copy GET-like mapping into target (last value wins for lists)."""
    if blob is None:
        return
    try:
        if hasattr(blob, "keys") and hasattr(blob, "__getitem__"):
            for k in blob.keys():
                if hasattr(blob, "getlist"):
                    lst = blob.getlist(k)
                    val = _last_nonempty_from_sequence(lst or [])
                else:
                    val = blob[k]
                    if isinstance(val, (list, tuple)):
                        val = _last_nonempty_from_sequence(val)
                # Never overwrite a good query param with blank (Peliqan sometimes
                # exposes partial MultiDicts that omit scherm or set "").
                if not _is_nonempty_scalar(val) and k in target and _is_nonempty_scalar(
                    target.get(k)
                ):
                    continue
                target[k] = val
    except Exception:
        pass


def _merge_query_string_into_target(target, query_string):
    """Parse a raw query string and merge into target (later keys overwrite)."""
    if not query_string:
        return
    if isinstance(query_string, bytes):
        query_string = query_string.decode("utf-8", errors="replace")
    if not isinstance(query_string, str) or not query_string.strip():
        return
    parsed = parse_qs(query_string.strip(), keep_blank_values=True)
    for k, v in parsed.items():
        val = _last_nonempty_from_sequence(v) if isinstance(v, list) else v
        if (
            not _is_nonempty_scalar(val)
            and k in target
            and _is_nonempty_scalar(target.get(k))
        ):
            continue
        target[k] = val


def parse_query(request):
    """
    Peliqan may wrap the HTTP request differently per runtime.
    Merge ALL plausible sources — do *not* return early after a partial dict
    (e.g. `args` with only `bundle` would hide `scherm` from QUERY_STRING).
    """
    out = {}

    if request is None:
        return out

    # Peliqan contract (docs.peliqan.io/publish-apis): request is a plain dict
    #   {method, url, path, query_string, headers, data, form}
    # The GET params live in request['query_string'] (and in request['url']).
    if isinstance(request, dict):
        for key in ("query", "query_params", "queryStringParameters", "params"):
            blob = request.get(key)
            if isinstance(blob, dict):
                _merge_query_dict(out, blob)
        for key in ("query_string", "queryString", "raw_query_string"):
            _merge_query_string_into_target(out, request.get(key))
        for key in ("url", "full_url", "uri", "request_uri", "path"):
            url = request.get(key)
            if isinstance(url, str) and "?" in url:
                _merge_query_string_into_target(out, urlparse(url).query)
        # Fallback: gateway handed us the params directly (no envelope keys)
        envelope_keys = {"method", "url", "path", "query_string", "headers", "data", "form"}
        if not out and not (envelope_keys & set(request.keys())):
            _merge_query_dict(out, request)
        return out

    # WSGI / ASGI env (some hosts only expose query here)
    try:
        env = getattr(request, "environ", None) or getattr(
            request, "scope", None
        )
        if isinstance(env, dict):
            _merge_query_string_into_target(out, env.get("QUERY_STRING", ""))
    except Exception:
        pass

    # Framework wrappers first (often partial — can wrongly include scherm="")
    for attr in ("query_params", "args", "GET", "params", "query"):
        blob = getattr(request, attr, None)
        if blob is not None:
            _merge_query_dict(out, blob)

    # Multipart: request.keys() / get
    if hasattr(request, "get"):
        try:
            for key in request.keys():
                val = request.get(key)
                if val is not None and str(val).strip() != "":
                    _merge_query_dict(out, {key: val})
        except Exception:
            pass

    # Raw query string attribute
    raw = getattr(request, "query_string", None)
    _merge_query_string_into_target(out, raw)

    # AUTHORITATIVE: real HTTP GET string and full URL (merge LAST so they win)
    qs_env = os.environ.get("QUERY_STRING", "")
    _merge_query_string_into_target(out, qs_env)

    for url_attr in ("url", "full_url", "uri", "request_uri"):
        url = getattr(request, url_attr, None)
        if isinstance(url, str) and "?" in url:
            qpart = urlparse(url).query
            _merge_query_string_into_target(out, qpart)

    return out


def sql_str_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def load_tegel_config(scherm):
    rel = kpi_relation("kpi_tegel_config")
    scherm_lit = sql_str_literal(scherm)
    q = f"""
        SELECT *
        FROM {rel}
        WHERE scherm IN ('header', {scherm_lit})
        ORDER BY scherm, positie
    """
    df, err = fetch(q, "tegel_config")
    return df, err


def collect_trend_keys(config_rows):
    pairs = set()
    for row in config_rows:
        code = row.get("trend_kpi_code")
        if not code or (isinstance(code, float) and pd.isna(code)):
            continue
        scope = row.get("trend_scope_code")
        if scope is None or (isinstance(scope, float) and pd.isna(scope)):
            scope = ""
        pairs.add((str(code).strip(), str(scope).strip()))
    return pairs


def load_kpi_oordeel():
    df, err = fetch_table("kpi_oordeel")
    return df, err


def load_kpi_registry():
    df, err = fetch_table("kpi_registry")
    return df, err


def load_kpi_controles():
    df, err = fetch_table("kpi_controles")
    return df, err


def load_kpi_trend_filtered(pairs):
    if not pairs:
        return pd.DataFrame(), None
    rel = kpi_relation("kpi_trend")
    clauses = []
    for code, scope in pairs:
        scope_lit = sql_str_literal(scope)
        code_lit = sql_str_literal(code)
        clauses.append(
            f"(kpi_code = {code_lit} AND COALESCE(scope_code, '') = {scope_lit})"
        )
    where = " OR ".join(clauses)
    q = f"""
        SELECT *
        FROM {rel}
        WHERE {where}
        ORDER BY kpi_code, scope_code, serie, periode, volgnummer
    """
    df, err = fetch(q, "kpi_trend")
    return df, err


def screen_needs_omzetbrug(config_rows):
    for row in config_rows:
        code = str(row.get("kpi_code") or "").strip()
        if code == "omzet_brug":
            return True
        drill = str(row.get("drill_views") or "")
        if "kpi_omzetbrug" in drill:
            return True
    return False


def controles_summary(rows):
    summary = {"fout": 0, "let_op": 0, "ok": 0}
    for row in rows:
        status = str(row.get("status") or "").lower().strip()
        if status == "fout":
            summary["fout"] += 1
        elif status in ("let_op", "let op"):
            summary["let_op"] += 1
        elif status == "ok":
            summary["ok"] += 1
    return summary


def bundle_screen(q):
    scherm = str(q.get("scherm", "")).lower().strip()
    if scherm not in SCREENS:
        out = {
            "error": "invalid_scherm",
            "message": f"scherm must be one of: {', '.join(sorted(SCREENS))}",
            "handler_version": HANDLER_VERSION,
            "scherm_received": q.get("scherm"),
            "parsed_keys": sorted(q.keys()),
        }
        return out

    errors = []
    df_cfg, err = load_tegel_config(scherm)
    if err:
        errors.append({"table": "kpi_tegel_config", "error": err})

    config_rows = df_records(df_cfg)

    df_oordeel, err = load_kpi_oordeel()
    if err:
        errors.append({"table": "kpi_oordeel", "error": err})

    df_registry, err = load_kpi_registry()
    if err:
        errors.append({"table": "kpi_registry", "error": err})

    df_controles, err = load_kpi_controles()
    if err:
        errors.append({"table": "kpi_controles", "error": err})

    trend_pairs = collect_trend_keys(config_rows)
    df_trend, err = load_kpi_trend_filtered(trend_pairs)
    if err:
        errors.append({"table": "kpi_trend", "error": err})

    controles_rows = df_records(df_controles)

    kpi_omzetbrug = []
    if screen_needs_omzetbrug(config_rows):
        df_ob, err_ob = fetch_table("kpi_omzetbrug")
        if err_ob:
            errors.append({"table": "kpi_omzetbrug", "error": err_ob})
        else:
            kpi_omzetbrug = df_records(df_ob)

    out = {
        "bundle": "screen",
        "scherm": scherm,
        "tegel_config": config_rows,
        "kpi_oordeel": df_records(df_oordeel),
        "kpi_registry": df_records(df_registry),
        "kpi_trend": df_records(df_trend),
        "kpi_controles": controles_rows,
        "controles_summary": controles_summary(controles_rows),
        "errors": errors,
        "meta": {
            "warehouse": WAREHOUSE_DW,
            "handler_version": HANDLER_VERSION,
            "trend_filter_count": len(trend_pairs),
        },
    }
    if kpi_omzetbrug:
        out["kpi_omzetbrug"] = kpi_omzetbrug
    return out


def bundle_controles(_q):
    df, err = load_kpi_controles()
    rows = df_records(df)
    out = {
        "bundle": "controles",
        "kpi_controles": rows,
        "controles_summary": controles_summary(rows),
        "meta": {"warehouse": WAREHOUSE_DW, "handler_version": HANDLER_VERSION},
    }
    if err:
        out["errors"] = [{"table": "kpi_controles", "error": err}]
    return out


def bundle_registry(_q):
    df, err = load_kpi_registry()
    out = {
        "bundle": "registry",
        "kpi_registry": df_records(df),
        "meta": {"warehouse": WAREHOUSE_DW, "handler_version": HANDLER_VERSION},
    }
    if err:
        out["errors"] = [{"table": "kpi_registry", "error": err}]
    return out


def sanitize_view_name(name):
    name = str(name).strip()
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        return None
    if name not in ALLOWED_DRILL_VIEWS:
        return None
    return name


def _parse_periode_van(raw):
    """'2026', '2026-03' or '2026-03-15' -> 'YYYY-MM-DD'; anything else -> None."""
    raw = str(raw or "").strip()
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$", raw)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1)
    if not (1900 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _drill_where(view, scope, periode_van):
    """Build WHERE clauses for the optional filters; returns (clauses, applied, ignored)."""
    clauses, applied, ignored = [], {}, {}
    if scope:
        if scope.lower() == "concern" and view in DRILL_CONCERN_IS_ALL:
            applied["scope"] = "concern (alle entiteiten)"
        elif view in DRILL_SCOPE_OTHER_COLUMN:
            col = DRILL_SCOPE_OTHER_COLUMN[view]
            clauses.append(f"COALESCE(t.{col}, '') = {sql_str_literal(scope)}")
            applied["scope"] = scope
        elif view in DRILL_SCOPE_CODE_VIEWS:
            clauses.append(f"COALESCE(t.scope_code, '') = {sql_str_literal(scope)}")
            applied["scope"] = scope
        elif view in DRILL_SCOPE_LABEL_VIEWS:
            label = SCOPE_CODE_TO_LABEL.get(scope.lower(), scope)
            clauses.append(
                f"LOWER(COALESCE(t.scope, '')) IN (LOWER({sql_str_literal(scope)}), LOWER({sql_str_literal(label)}))"
            )
            applied["scope"] = scope
        else:
            ignored["scope"] = "view_has_no_scope_column"
    if periode_van:
        period_col = DRILL_ORDER.get(view, (None, None))[0]
        if period_col:
            clauses.append(f"t.{period_col} >= DATE {sql_str_literal(periode_van)}")
            applied["periode_van"] = periode_van
        else:
            ignored["periode_van"] = "view_has_no_period_column"
    return clauses, applied, ignored


def fetch_drill_view(view, limit, scope, periode_van):
    """
    Ordered, SQL-limited fetch of one drill view.
    Returns (records, meta, error, warnings). Falls back to the pre-v7 behaviour
    (SELECT * + cut in Python) if the ordered query fails, so a renamed column can
    never take the drill down.
    """
    rel = kpi_relation(view)
    period_col, order_expr = DRILL_ORDER.get(view, (None, None))
    clauses, applied, ignored = _drill_where(view, scope, periode_van)
    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    order_sql = f"{order_expr}, t::text" if order_expr else "t::text"
    warnings = []

    q = f"SELECT t.* FROM {rel} AS t{where_sql} ORDER BY {order_sql} LIMIT {int(limit) + 1}"
    df, err = fetch(q, view)
    fallback = False
    if err:
        warnings.append({"view": view, "warning": f"ordered_query_failed_fallback_unordered: {err[:300]}"})
        df, err = fetch_table(view)
        fallback = True
        if err:
            return [], None, err, warnings

    recs = df_records(df)
    truncated = len(recs) > limit
    if truncated:
        recs = recs[:limit]

    total_count = len(recs)
    if truncated and not fallback:
        df_n, err_n = fetch(f"SELECT COUNT(*) AS n FROM {rel} AS t{where_sql}", view + "_count")
        try:
            total_count = int(df_n.iloc[0, 0]) if not err_n and not df_n.empty else None
        except Exception:
            total_count = None
    elif truncated and fallback:
        total_count = len(df) if df is not None else None

    meta = {
        "row_count": len(recs),
        "truncated": truncated,
        "total_count": total_count,
        "limit": limit,
        "order_by": None if fallback else (order_expr or "").replace("t.", ""),
        "ordered": not fallback,
        "filters": applied,
    }
    if ignored:
        meta["filters_ignored"] = ignored
    return recs, meta, None, warnings


def bundle_drill(q):
    raw = str(q.get("views", "")).strip()
    if not raw:
        return {"error": "missing_views", "message": "views query param required"}

    try:
        limit = int(q.get("limit", 2000))
    except (TypeError, ValueError):
        limit = 2000
    limit = max(1, min(limit, 5000))

    views = []
    for part in raw.split(","):
        v = sanitize_view_name(part)
        if v:
            views.append(v)

    if not views:
        return {"error": "invalid_views", "message": "no allowed view names in views param"}

    errors = []
    scope = str(q.get("scope", "") or "").strip()[:64]
    periode_raw = str(q.get("periode_van", "") or "").strip()
    periode_van = _parse_periode_van(periode_raw) if periode_raw else None
    if periode_raw and not periode_van:
        errors.append({"view": "*", "warning": f"periode_van_ignored_invalid: {periode_raw[:40]}"})

    tables = {}
    table_meta = {}
    for view in views:
        recs, meta, err, warnings = fetch_drill_view(view, limit, scope, periode_van)
        errors.extend(warnings)
        if err:
            errors.append({"view": view, "error": err})
            tables[view] = []
            table_meta[view] = {"row_count": 0, "truncated": False, "total_count": None, "limit": limit, "error": True}
            continue
        tables[view] = recs
        table_meta[view] = meta
        if meta["truncated"]:
            # Same entry as before v7, kept for clients that read errors[].
            errors.append({"view": view, "warning": f"truncated_to_{limit}_rows"})

    return {
        "bundle": "drill",
        "views": views,
        "tables": tables,
        "table_meta": table_meta,
        "errors": errors,
        "meta": {
            "warehouse": WAREHOUSE_DW,
            "handler_version": HANDLER_VERSION,
            "limit": limit,
            "filters": {k: v for k, v in (("scope", scope), ("periode_van", periode_van)) if v},
        },
    }


def resolve_bundle(q):
    b = str(q.get("bundle", "screen")).lower().strip()
    if b not in ("screen", "controles", "drill", "registry"):
        return "screen"
    return b


def handler(request):
    q = parse_query(request)
    bundle = resolve_bundle(q)

    if bundle == "controles":
        return bundle_controles(q)
    if bundle == "registry":
        return bundle_registry(q)
    if bundle == "drill":
        return bundle_drill(q)
    return bundle_screen(q)
