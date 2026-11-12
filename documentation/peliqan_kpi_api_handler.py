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
HANDLER_VERSION = "2026-11-06-kpi-v6-request-dict-query-string"

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
        "kpi_acc_dossiers_maand",
        "kpi_acc_doorlooptijd_maand",
        "kpi_onboarding_kwartaal",
        "kpi_d2s_maand",
        "kpi_awc_ops_maand",
        "kpi_awc_schade_klant",
        "kpi_afc_sprinter_maand",
        "kpi_afc_zending_maand",
        "kpi_afc_eigenaar_maand",
        "kpi_afc_klant_jaar",
        "kpi_afc_klant",
        "kpi_afc_klant_retentie_jaar",
        "kpi_afc_resultaat_maand",
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

    tables = {}
    errors = []
    for view in views:
        df, err = fetch_table(view)
        if err:
            errors.append({"view": view, "error": err})
            tables[view] = []
        else:
            recs = df_records(df)
            if len(recs) > limit:
                tables[view] = recs[:limit]
                errors.append(
                    {"view": view, "warning": f"truncated_to_{limit}_rows"}
                )
            else:
                tables[view] = recs

    return {
        "bundle": "drill",
        "views": views,
        "tables": tables,
        "errors": errors,
        "meta": {"warehouse": WAREHOUSE_DW, "handler_version": HANDLER_VERSION},
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
