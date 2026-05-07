# AWC dashboard — Peliqan API handler (reference implementation)
#
# Use in Peliqan:
#   1. Build → Apps → add script → type "API endpoint handler".
#   2. Replace the editor content with this file (or merge the parts you need).
#   3. Build → API endpoints → add route, Method GET, attach this app, JWT on.
#   4. Suggested route: /awc/data  →  Laravel calls:
#        GET https://api.eu.peliqan.io/{your_id}/awc/data?bundle=wms
#        Authorization: JWT {token}
#
# Query parameter:
#   bundle = wms | hubspot | finance | all   (default: all)
#
# Peliqan calls handler(request) for each HTTP request (current API runtime).
# Return a JSON-serializable dict — Peliqan turns it into the response body.
# If bundle is always "all", print(request) once to see the real query shape and extend resolve_bundle_name_from_request.
#
# Sources match documentation/PELIQAN_AWC_DASHBOARD.md (Streamlit app).

import json
from urllib.parse import parse_qs

import pandas as pd

# --- Warehouse ids: must match Peliqan database / connection ids exactly (case-sensitive). ---
# Tip: in a Peliqan script run  pq.list_databases()  or check Build → data sources for the real ids.
WAREHOUSE_HS = "dw_2401"
WAREHOUSE_7T = "db_7t"
AWC_ADMIN_CODE = "alaw"

# --- DB connections ---
dbconn_hs = pq.dbconnect(WAREHOUSE_HS)

_7T_BESCHIKBAAR = False
dbconn_7t = None
_7T_PROBE_ERROR = None
try:
    dbconn_7t = pq.dbconnect(WAREHOUSE_7T)
    _probe = dbconn_7t.fetch(WAREHOUSE_7T, query="SELECT 1 AS ok", df=True)
    if _probe is not None and not _probe.empty:
        _7T_BESCHIKBAAR = True
    else:
        _7T_PROBE_ERROR = "7T probe query returned no rows (check warehouse id and DB access)."
except Exception as e:
    dbconn_7t = None
    _7T_BESCHIKBAAR = False
    _7T_PROBE_ERROR = f"{type(e).__name__}: {e}"


def fetch_hs(query):
    df = dbconn_hs.fetch(WAREHOUSE_HS, query=query, df=True)
    return df if df is not None else pd.DataFrame()


def fetch_7t(query):
    if not _7T_BESCHIKBAAR or dbconn_7t is None:
        return pd.DataFrame()
    df = dbconn_7t.fetch(WAREHOUSE_7T, query=query, df=True)
    return df if df is not None else pd.DataFrame()


def df_records(df):
    """Serialize DataFrame to JSON-serializable list of dicts (ISO dates)."""
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def load_bezetting_raw():
    df_totaal = fetch_7t(
        """
        SELECT
            mpc.ID                              AS locatie_id,
            mpc.Naam                            AS locatienaam,
            mpc.Magazijn_ID                     AS magazijn_id,
            ISNULL(mps.Aantal_Palletplaatsen,1) AS palletplaatsen,
            mpc.Geblokkeerd_Voor_Picken         AS geblokkeerd
        FROM dbo.Magazijn_Plaatscodes  AS mpc
        LEFT JOIN dbo.Magazijn_Plaatssoorten AS mps
               ON mpc.Magazijn_Plaatssoort_ID = mps.ID
        INNER JOIN dbo.Magazijnen AS mag
               ON mpc.Magazijn_ID = mag.ID
        INNER JOIN dbo.Administraties AS adm
               ON mag.Administratie_ID = adm.ID
        WHERE mpc.Extern = 0
          AND adm.Code = 'alaw'
    """
    )
    df_bezet = fetch_7t(
        """
        SELECT
            aml.Magazijn_Plts_ID            AS locatie_id,
            COUNT(*)                        AS artikel_partijen,
            SUM(aml.Technische_Voorraad)    AS voorraad_totaal
        FROM dbo.Artikel_Magazijnlocaties AS aml
        WHERE aml.Technische_Voorraad > 0
          AND aml.Er_Is_Voorraad = 1
        GROUP BY aml.Magazijn_Plts_ID
    """
    )
    return df_totaal, df_bezet


def load_ontvangsten():
    return fetch_7t(
        """
        SELECT
            o.ID                        AS ontvangst_id,
            o.Datum                     AS ontvangst_datum,
            o.Aankomst_Leverancier      AS aankomst_leverancier,
            o.Ontvangst_Definitief      AS definitief,
            o.Relatie_ID                AS klant_id,
            o.MutatieDatum              AS mutatie_datum,
            o.Status                    AS status,
            o.Administratie_ID          AS administratie_id
        FROM dbo.Ontvangsten AS o
        INNER JOIN dbo.Administraties AS adm
               ON o.Administratie_ID = adm.ID
        WHERE o.Datum >= DATEADD(day, -730, GETDATE())
          AND adm.Code = 'alaw'
    """
    )


def load_tellingen():
    return fetch_7t(
        """
        SELECT
            tl.ID                           AS telling_locatie_id,
            tl.Telling_ID                   AS telling_id,
            tl.Totaal_Aantal_Verwacht       AS verwacht,
            tl.Totaal_Aantal_Geteld         AS geteld,
            tl.Totaal_Aantal_Correctie      AS correctie,
            tl.Telling_Gereed               AS gereed,
            tl.Datum_Telling_Gereed         AS teldatum
        FROM dbo.Telling_Locaties AS tl
        INNER JOIN dbo.Tellingen AS t
               ON tl.Telling_ID = t.ID
        INNER JOIN dbo.Administraties AS adm
               ON t.Administratie_ID = adm.ID
        WHERE tl.Telling_Gereed = 1
          AND tl.Datum_Telling_Gereed >= DATEADD(day, -730, GETDATE())
          AND adm.Code = 'alaw'
    """
    )


def load_leverdata():
    return fetch_7t(
        """
        SELECT
            ld.ID                       AS id,
            ld.Orderregel_ID            AS orderregel_id,
            ld.Informatief              AS informatief,
            ld.Oude_Leverdatum          AS gepland,
            ld.Nieuwe_Leverdatum        AS werkelijk,
            ld.MutatieDatum             AS mutatie_datum
        FROM dbo.Orderregel_Leverdata AS ld
        INNER JOIN dbo.Orderregels AS orr
               ON ld.Orderregel_ID = orr.ID
        INNER JOIN dbo.Orders AS ord
               ON orr.Order_ID = ord.ID
        INNER JOIN dbo.Administraties AS adm
               ON ord.Administratie_ID = adm.ID
        WHERE ld.MutatieDatum >= DATEADD(day, -730, GETDATE())
          AND adm.Code = 'alaw'
    """
    )


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
        """
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
        WHERE lm.admin_code = 'alaw'
    """
    )


def load_cashweb_saldi():
    # period_amounts_* can be tilde-separated period lists (e.g. "0.00~9716.00~…");
    # casting the whole string to NUMERIC fails — return as text and parse in the app if needed.
    return fetch_hs(
        """
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
        WHERE lb.admin_code = 'alaw'
    """
    )


def bundle_wms():
    totaal_df, bezet_df = load_bezetting_raw()
    return {
        "wms_available": _7T_BESCHIKBAAR,
        "bezetting": {
            "locaties_totaal": df_records(totaal_df),
            "locaties_bezet": df_records(bezet_df),
        },
        "ontvangsten": df_records(load_ontvangsten()),
        "tellingen": df_records(load_tellingen()),
        "leverdata": df_records(load_leverdata()),
    }


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


def resolve_bundle_name_from_request(request):
    """Read ?bundle=wms|hubspot|finance|all from the object Peliqan passes to handler(request)."""
    name = None
    try:
        if request is None:
            return "all"

        if isinstance(request, dict):
            if isinstance(request.get("query"), dict):
                name = request["query"].get("bundle")
            elif isinstance(request.get("query_params"), dict):
                name = request["query_params"].get("bundle")
            elif isinstance(request.get("queryStringParameters"), dict):
                v = request["queryStringParameters"].get("bundle")
                name = v[0] if isinstance(v, (list, tuple)) and v else v

            if name is None:
                qs = (
                    request.get("query_string")
                    or request.get("queryString")
                    or request.get("raw_query_string")
                )
                if isinstance(qs, str) and qs.strip():
                    parsed = parse_qs(qs.lstrip("?"))
                    b = parsed.get("bundle")
                    if b:
                        name = b[0]

            if name is None:
                url = request.get("url") or request.get("path", "")
                if isinstance(url, str) and "?" in url:
                    parsed = parse_qs(url.split("?", 1)[1])
                    b = parsed.get("bundle")
                    if b:
                        name = b[0]
        else:
            if hasattr(request, "args"):
                name = request.args.get("bundle")
            elif hasattr(request, "query_params"):
                qp = request.query_params
                if hasattr(qp, "get"):
                    name = qp.get("bundle")

        if name is None:
            return "all"
        name = str(name).lower()
    except Exception:
        return "all"

    allowed = {"wms", "hubspot", "finance", "all"}
    return name if name in allowed else "all"


def build_payload(bundle_name="all"):
    name = str(bundle_name).lower()
    allowed = {"wms", "hubspot", "finance", "all"}
    if name not in allowed:
        name = "all"
    out = {
        "bundle": name,
        "meta": {
            "warehouses": {"hubspot": WAREHOUSE_HS, "wms": WAREHOUSE_7T},
            "wms": {
                "available": _7T_BESCHIKBAAR,
                "probe_error": _7T_PROBE_ERROR,
            },
        },
    }
    if name == "wms":
        out["data"] = bundle_wms()
    elif name == "hubspot":
        out["data"] = bundle_hubspot()
    elif name == "finance":
        out["data"] = bundle_finance()
    else:
        out["data"] = {
            "wms": bundle_wms(),
            "hubspot": bundle_hubspot(),
            "finance": bundle_finance(),
        }
    return out


def handler(request):
    """Required entrypoint for Peliqan published API endpoints."""
    bundle = resolve_bundle_name_from_request(request)
    return build_payload(bundle_name=bundle)
