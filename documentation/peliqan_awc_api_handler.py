# AWC dashboard — Peliqan API handler (HubSpot + finance from dw_2401)
#
# Use in Peliqan:
#   1. Build → Apps → add script → type "API endpoint handler".
#   2. Replace the editor content with this file.
#   3. Build → API endpoints → add route, Method GET, attach this app, JWT on.
#   4. Suggested route: /awc/data  →  Laravel calls:
#        GET https://api.eu.peliqan.io/{your_id}/awc/data?bundle=all
#        Authorization: JWT {token}
#
# Query parameters:
#   bundle = hubspot | finance | all   (default: all)
#
# 7T WMS moved out: it lives in peliqan_7t_api_handler.py (direct SQL Server,
# its own endpoint) because Trino was slow and its latency/caching profile is
# very different from these dw_2401 warehouse reads. This handler only serves
# HubSpot (tickets / NPS / cargosnap) and finance (cashweb) from dw_2401.

import json
from urllib.parse import parse_qs

import pandas as pd

# --- Warehouse id: must match the Peliqan database id exactly (case-sensitive). ---
WAREHOUSE_HS = "dw_2401"

# AWC administratie selector for cashweb (admin_code on dw_2401 tables).
AWC_ADMIN_CODE = "alaw"

# Bump on redeploy — surfaces in API meta to confirm Peliqan has the latest script.
HANDLER_VERSION = "2026-06-11-awc-dw2401-v1"

# --- DB connection (lazy — import-time dbconnect can 500 the whole endpoint) ---
_dbconn_hs = None


def _get_hs_conn():
    global _dbconn_hs
    if _dbconn_hs is None:
        _dbconn_hs = pq.dbconnect(WAREHOUSE_HS)
    return _dbconn_hs


def fetch_hs(query):
    df = _get_hs_conn().fetch(WAREHOUSE_HS, query=query, df=True)
    return df if df is not None else pd.DataFrame()


def df_records(df):
    """Serialize DataFrame to a JSON-serializable list of dicts (ISO dates)."""
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def load_tickets():
    return fetch_hs(
        """
        SELECT
            t.id,
            t.createdat                     AS aangemaakt_op,
            t.subject                       AS onderwerp,
            COALESCE(ps.label,
                     t.hs_pipeline_stage)   AS status,
            t.hs_ticket_priority            AS prioriteit,
            t.hs_pipeline                   AS pipeline,
            t.category_issue                AS categorie,
            t.closed_date                   AS gesloten_op,
            t.time_to_close                 AS time_to_close,
            t.time_to_first_agent_reply     AS time_to_first_reply
        FROM hubspot_v2.tickets AS t
        LEFT JOIN hubspot_v2.tickets_pipeline__stages AS ps
            ON t.hs_pipeline_stage = ps.id
    """
    )


def load_nps():
    return fetch_hs(
        """
        SELECT
            id,
            hs_value                                      AS score,
            hs_response_group                             AS groep,
            hs_survey_type                                AS survey_type,
            would_you_recommend_our_services_to_others_  AS score_fallback,
            createdat                                     AS ingevuld_op
        FROM hubspot_v2.feedback_submissions
    """
    )


def load_cargosnap_schade():
    return fetch_hs(
        """
        SELECT
            u.id                        AS upload_id,
            u.file_id,
            u.created_at,
            u.has_damage,
            u.damage_type_desc          AS schade_type,
            u.document_type_desc        AS document_type,
            u.workflow_description      AS workflow,
            u.workflow_step_description AS workflow_stap,
            f.scan_code,
            f.snap_count,
            f.snap_count_with_damage
        FROM cargosnap.uploads AS u
        LEFT JOIN cargosnap.files AS f ON u.file_id = f.id
    """
    )


def load_cashweb_mutaties():
    return fetch_hs(
        f"""
        SELECT
            lm.book_date            AS boekdatum,
            lm.book_period          AS periode,
            lm.book_quarter         AS kwartaal,
            lm.book_year            AS boekjaar,
            lm.account_number       AS rekeningnummer,
            lm.description          AS omschrijving,
            lm.debit_credit         AS dc,
            CAST(REPLACE(lm.amount, ',', '.') AS NUMERIC(18,2)) AS bedrag,
            lm.journal_code         AS dagboek,
            lm.relation_number      AS relatienummer,
            lm.sub_administration   AS subadministratie,
            lm.admin_code           AS admin_code
        FROM cashweb.ledger_mutations AS lm
        WHERE lm.admin_code = '{AWC_ADMIN_CODE}'
    """
    )


def load_cashweb_saldi():
    # period_amounts_* can be tilde-separated period lists (e.g. "0.00~9716.00~…");
    # casting the whole string to NUMERIC fails — return as text and parse in the app.
    return fetch_hs(
        f"""
        SELECT
            lb.book_year                                    AS boekjaar,
            lb.account_number                               AS rekeningnummer,
            lb.description                                  AS omschrijving,
            lb.exploitation_code                            AS exploitatie_code,
            lb.sub_administration                           AS subadministratie,
            lb.admin_code                                   AS admin_code,
            lb.period_amounts_debit                         AS periode_debet,
            lb.period_amounts_credit                        AS periode_credit,
            lb.period_amounts_result                        AS periode_resultaat
        FROM cashweb.ledger_balances AS lb
        WHERE lb.admin_code = '{AWC_ADMIN_CODE}'
    """
    )


def bundle_hubspot():
    return {
        "tickets": df_records(load_tickets()),
        "nps": df_records(load_nps()),
        "cargosnap_uploads": df_records(load_cargosnap_schade()),
    }


def bundle_finance():
    return {
        "cashweb_mutaties": df_records(load_cashweb_mutaties()),
        "cashweb_saldi": df_records(load_cashweb_saldi()),
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


def resolve_bundle_name_from_request(request):
    """Read ?bundle=hubspot|finance|all from the object Peliqan passes to handler(request)."""
    name = str(_query_param(request, "bundle", "all")).lower()
    allowed = {"hubspot", "finance", "all"}
    return name if name in allowed else "all"


def build_payload(bundle_name="all", request=None):
    name = str(bundle_name).lower()
    allowed = {"hubspot", "finance", "all"}
    if name not in allowed:
        name = "all"
    meta = {
        "handler_version": HANDLER_VERSION,
        "source": "dw_2401",
        "warehouses": {"hubspot": WAREHOUSE_HS, "finance": WAREHOUSE_HS},
        "note": "7T WMS lives on its own endpoint (peliqan_7t_api_handler.py).",
    }
    if name == "hubspot":
        data = bundle_hubspot()
    elif name == "finance":
        data = bundle_finance()
    else:
        data = {
            "hubspot": bundle_hubspot(),
            "finance": bundle_finance(),
        }
    return {"bundle": name, "meta": meta, "data": data}


def handler(request):
    """Required entrypoint for Peliqan published API endpoints."""
    try:
        bundle = resolve_bundle_name_from_request(request)
        return build_payload(bundle_name=bundle, request=request)
    except Exception as e:
        return {
            "status": "error",
            "message": f"{type(e).__name__}: {e}",
            "bundle": resolve_bundle_name_from_request(request),
            "meta": {"handler_version": HANDLER_VERSION},
        }
