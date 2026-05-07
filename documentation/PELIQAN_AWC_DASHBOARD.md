import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# AMSTERDAM WAREHOUSE CO — KPI Dashboard
# AWC · Warehouse Operations via 7T Software + HubSpot
# Databronnen: dw_2401 (hubspot_v2) · db_7t (dbo)
# KPI-structuur: AWC___KPI_Structuur.xlsx / sheet "AWC"
# ============================================================

st.set_page_config(
    page_title="AWC — Warehouse KPI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── AWC brand styling ─────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
      font-family: 'Barlow', sans-serif;
      background-color: #F4F5F7;
      color: #1A1A1A;
  }
  .awc-header {
      background: #000;
      margin: 1.5rem -1rem 0 -1rem;
      padding: 14px 28px;
      display: flex; align-items: center; justify-content: space-between;
      border-bottom: 3px solid #FF6B1A;
  }
  .awc-logo-text {
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 800; font-size: 1.35rem;
      letter-spacing: 0.04em; text-transform: uppercase;
      color: #fff; line-height: 1.1;
  }
  .awc-logo-sub {
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 600; font-size: 0.6rem;
      letter-spacing: 0.22em; text-transform: uppercase;
      color: #FF6B1A; margin-top: 1px;
  }
  .awc-header-right { font-size: 0.78rem; color: #888; letter-spacing: 0.04em; }
  .awc-header-right span {
      background: #FF6B1A; color: #fff; font-weight: 600;
      padding: 3px 10px; border-radius: 4px; margin-left: 10px;
      font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase;
  }
  .awc-subbar {
      background: #fff; margin: 0 -1rem 1.5rem -1rem;
      padding: 10px 28px; border-bottom: 1px solid #E2E5EA;
      display: flex; align-items: center; gap: 8px;
  }
  .awc-subbar-title {
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 700; font-size: 1.3rem;
      letter-spacing: 0.01em; color: #1A1A1A; text-transform: uppercase;
  }
  .co-pill {
      background: #F0F0F0; color: #444;
      font-size: 0.68rem; font-weight: 600;
      letter-spacing: 0.08em; text-transform: uppercase;
      padding: 3px 9px; border-radius: 3px; margin-left: 4px;
      border: 1px solid #DDDDE0;
  }
  .co-pill.active { background: #FF6B1A; color: #fff; border-color: #FF6B1A; }

  section[data-testid="stSidebar"] {
      background-color: #000 !important; border-right: none !important;
  }
  section[data-testid="stSidebar"] * { color: #CCC !important; }
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 {
      color: #fff !important;
      font-family: 'Barlow Condensed', sans-serif !important;
      text-transform: uppercase; letter-spacing: 0.08em;
  }

  h1 { font-family: 'Barlow Condensed', sans-serif !important;
       font-weight: 800 !important; text-transform: uppercase;
       letter-spacing: 0.02em; color: #1A1A1A !important; }
  h2 { font-family: 'Barlow Condensed', sans-serif !important;
       font-weight: 700 !important; color: #1A1A1A !important; font-size: 1.15rem !important; }
  h3 { font-family: 'Barlow', sans-serif !important;
       font-weight: 600 !important; color: #333 !important; font-size: 1rem !important; }

  [data-testid="metric-container"] {
      background: #fff; border: 1px solid #E2E5EA;
      border-left: 4px solid #FF6B1A; border-radius: 4px;
      padding: 16px 18px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  [data-testid="stMetricLabel"] {
      color: #666 !important; font-size: 0.72rem !important;
      text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600 !important;
  }
  [data-testid="stMetricValue"] {
      color: #000 !important;
      font-family: 'Barlow Condensed', sans-serif !important;
      font-weight: 800 !important; font-size: 2.1rem !important;
  }
  [data-testid="stMetricDelta"] { font-size: 0.8rem !important; font-weight: 600 !important; }
  [data-testid="stMetricDelta"] svg { display: none; }

  .stTabs [data-baseweb="tab-list"] {
      background: #fff; border-radius: 0; gap: 0; padding: 0;
      border-bottom: 2px solid #E2E5EA;
  }
  .stTabs [data-baseweb="tab"] {
      font-family: 'Barlow', sans-serif; font-weight: 600; font-size: 0.85rem;
      color: #888 !important; border-radius: 0; padding: 10px 20px;
      background: transparent !important;
      border-bottom: 3px solid transparent; margin-bottom: -2px;
  }
  .stTabs [aria-selected="true"] {
      color: #000 !important; border-bottom: 3px solid #FF6B1A !important;
      background: transparent !important;
  }

  hr { border-color: #E2E5EA !important; margin: 20px 0; }
  [data-testid="stDataFrame"] {
      border: 1px solid #E2E5EA; border-radius: 4px; overflow: hidden; background: #fff;
  }
  .kpi-badge {
      display: inline-block; background: #000; color: #fff;
      font-family: 'Barlow Condensed', sans-serif; font-weight: 700;
      font-size: 0.65rem; letter-spacing: 0.14em; text-transform: uppercase;
      padding: 3px 10px; border-radius: 2px; margin-bottom: 12px;
  }
  .kpi-badge.orange { background: #FF6B1A; }
  .block-container { padding-top: 2rem !important; }
  .src-pill {
      display: inline-block; font-size: 0.65rem; font-weight: 700;
      letter-spacing: 0.10em; text-transform: uppercase;
      padding: 2px 8px; border-radius: 2px; margin-left: 6px; vertical-align: middle;
  }
  .src-7t   { background: #1A2B4A; color: #fff; }
  .src-hs   { background: #FF7A59; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
now_str = datetime.now().strftime("%A %d %B %Y")
st.markdown(f"""
<div class="awc-header">
  <div>
    <div class="awc-logo-text">Amsterdam<br>Warehouse Co</div>
    <div class="awc-logo-sub">The place to go</div>
  </div>
  <div class="awc-header-right">
    Data &amp; Application Platform &nbsp;·&nbsp; {now_str}
    <span>Warehouse KPI's</span>
  </div>
</div>
<div class="awc-subbar">
  <div class="awc-subbar-title">AWC KPI Dashboard</div>
  <span class="co-pill active">AWC</span>
  <span class="co-pill">7T Software</span>
  <span class="co-pill">HubSpot</span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.markdown(
    '<div style="font-family:\'Barlow Condensed\',sans-serif;font-weight:800;'
    'font-size:1.1rem;letter-spacing:0.08em;text-transform:uppercase;color:#fff;'
    'border-bottom:1px solid #2a2a2a;padding-bottom:10px;margin-bottom:4px;">'
    'Filters</div>',
    unsafe_allow_html=True,
)

PERIODE_OPTIES = {
    "Afgelopen 7 dagen":   7,
    "Afgelopen 30 dagen":  30,
    "Afgelopen 90 dagen":  90,
    "Afgelopen 12 maanden": 365,
    "Aangepaste periode":  None,
}
gekozen_periode = st.sidebar.selectbox("Periode", list(PERIODE_OPTIES.keys()), index=1)

if gekozen_periode == "Aangepaste periode":
    start_datum = st.sidebar.date_input("Startdatum", value=datetime.today() - timedelta(days=30))
    eind_datum  = st.sidebar.date_input("Einddatum",  value=datetime.today())
else:
    dagen       = PERIODE_OPTIES[gekozen_periode]
    eind_datum  = datetime.today().date()
    start_datum = eind_datum - timedelta(days=dagen)

start_dt       = pd.Timestamp(start_datum)
eind_dt        = pd.Timestamp(eind_datum) + pd.Timedelta(days=1)
periode_lengte = (eind_dt - start_dt).days

# ── DB connecties & helpers ───────────────────────────────────
WAREHOUSE_HS = 'dw_2401'
WAREHOUSE_7T = 'db_7t'   # zodra 7T in Peliqan staat werkt dit automatisch
AWC_ADMIN    = 'alaw'     # Administratiecode Amsterdam Warehouse Company in 7T

dbconn_hs = pq.dbconnect(WAREHOUSE_HS)

# 7T: probeer te verbinden; als de koppeling er nog niet is, werkt
# het dashboard gewoon verder — 7T-tabs tonen een placeholder.
_7T_BESCHIKBAAR = False
dbconn_7t = None
try:
    dbconn_7t = pq.dbconnect(WAREHOUSE_7T)
    # pq.dbconnect() slaagt altijd — testquery bepaalt of de DB echt bestaat
    _probe = dbconn_7t.fetch(WAREHOUSE_7T, query='SELECT 1 AS ok', df=True)
    _7T_BESCHIKBAAR = True
except Exception:
    dbconn_7t = None  # koppeling nog niet beschikbaar — tabs tonen placeholder

st.sidebar.markdown(f"**Van:** {start_datum}  \n**Tot:** {eind_datum}")
st.sidebar.markdown('<hr style="border-color:#222;margin:16px 0">', unsafe_allow_html=True)
_7t_label = "✅ Verbonden" if _7T_BESCHIKBAAR else "⏳ Binnenkort"
_7t_kleur = "#4CAF50"    if _7T_BESCHIKBAAR else "#888"
st.sidebar.markdown(
    f'<div style="font-size:0.7rem;letter-spacing:0.04em;line-height:2">'
    f'<b style="color:#fff;font-size:0.75rem">Databronnen</b><br>'
    f'<span style="color:{_7t_kleur}">●</span>'
    f' <b style="color:#ccc">7T Software</b>'
    f' <span style="color:{_7t_kleur};font-size:0.65rem">{_7t_label}</span><br>'
    f'<span style="color:#4CAF50">●</span>'
    f' <b style="color:#ccc">HubSpot</b>'
    f' <span style="color:#4CAF50;font-size:0.65rem">✅ Verbonden</span>'
    f'</div>',
    unsafe_allow_html=True,
)

def fetch_hs(query):
    """Haal data op uit HubSpot (dw_2401 / hubspot_v2)."""
    df = dbconn_hs.fetch(WAREHOUSE_HS, query=query, df=True)
    return df if df is not None else pd.DataFrame()

def fetch_7t(query):
    """Haal data op uit 7T Software WMS (db_7t / dbo).
    Geeft lege DataFrame terug als de koppeling nog niet beschikbaar is."""
    if not _7T_BESCHIKBAAR or dbconn_7t is None:
        return pd.DataFrame()
    df = dbconn_7t.fetch(WAREHOUSE_7T, query=query, df=True)
    return df if df is not None else pd.DataFrame()

def _7t_placeholder():
    """Toon een uniforme 'binnenkort beschikbaar' melding voor 7T-KPIs."""
    st.info(
        "⏳ **7T Software koppeling nog niet actief.**  \n"
        "Zodra de 7T-database is gekoppeld in Peliqan (warehouse: `db_7t`) "
        "verschijnt hier automatisch de live data.",
        icon=None,
    )

def delta_tekst(huidig, vorig, inverse=False):
    """Berekent periode-delta. inverse=True = lager is beter (bijv. doorlooptijd)."""
    try:
        h, v = float(huidig), float(vorig)
        if v > 0:
            pct = ((h - v) / v) * 100
            return f"{pct:+.1f}%"
    except Exception:
        pass
    return "n.v.t."

def ts(dt):
    return dt.tz_localize("UTC") if dt.tzinfo is None else dt

vorige_start = start_dt - pd.Timedelta(days=periode_lengte)
vorige_eind  = start_dt

freq = "D" if periode_lengte <= 31 else ("W" if periode_lengte <= 180 else "MS")

# ── Tabs ──────────────────────────────────────────────────────
(tab_samen, tab_bezet, tab_lead, tab_door,
 tab_kwal, tab_ticks, tab_nps, tab_fin) = st.tabs([
    "🏠 Samenvatting",
    "📦 Bezettingsgraad",
    "⏱ Doorlooptijd",
    "🚚 Doorvoer",
    "✅ Kwaliteit",
    "🎫 Tickets",
    "⭐ NPS",
    "💰 Financieel",
])


# ════════════════════════════════════════════════════════════
# GEDEELDE DATA — wordt in meerdere tabs gebruikt
# ════════════════════════════════════════════════════════════

# ── Bezetting: totaal locaties + bezette locaties ─────────────
@st.cache_data(ttl=3600)
def load_bezetting():
    """
    Bezettingsgraad = bezette palletplaatsen / totale palletplaatsen × 100%
    Bron: Magazijn_Plaatscodes (totaal) × Magazijn_Plaatssoorten.Aantal_Palletplaatsen
          Artikel_Magazijnlocaties (bezet, Technische_Voorraad > 0)
    """
    df_totaal = fetch_7t("""
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
    """)

    df_bezet = fetch_7t("""
        SELECT
            aml.Magazijn_Plts_ID            AS locatie_id,
            COUNT(*)                        AS artikel_partijen,
            SUM(aml.Technische_Voorraad)    AS voorraad_totaal
        FROM dbo.Artikel_Magazijnlocaties AS aml
        WHERE aml.Technische_Voorraad > 0
          AND aml.Er_Is_Voorraad = 1
        GROUP BY aml.Magazijn_Plts_ID
    """)
    return df_totaal, df_bezet

# ── Storage Lead Time: ontvangsten + definitief status ────────
@st.cache_data(ttl=3600)
def load_ontvangsten():
    """
    Dock-to-Stock / Storage Lead Time:
    Datum = aankomstdatum · Ontvangst_Definitief = 1 wanneer volledig ingeruimd
    Dagen = DATEDIFF(day, Datum, MutatieDatum) als proxy voor de inruimtijd.
    """
    df = fetch_7t("""
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
    """)
    return df

# ── Doorvoer: ontvangsten (inbound) ──────────────────────────
# (hergebruik van load_ontvangsten)

# ── Kwaliteit: tellingen (Inventory Accuracy) ─────────────────
@st.cache_data(ttl=3600)
def load_tellingen():
    """
    Inventory Accuracy = (locaties zonder verschil / totaal getelde locaties) × 100%
    Bron: Telling_Locaties
    """
    df = fetch_7t("""
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
    """)
    return df

# ── Leverdata: OTIF (On-Time In-Full) ─────────────────────────
@st.cache_data(ttl=3600)
def load_leverdata():
    """
    OTIF-proxy: orderregels waarbij de leverdatum NIET is verschoven (= on time)
    Bron: Orderregel_Leverdata (Oude vs. Nieuwe leverdatum)
          Ontvangst_Definitief op tijdige ontvangst
    """
    df = fetch_7t("""
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
    """)
    return df

# ── HubSpot Tickets ───────────────────────────────────────────
@st.cache_data(ttl=1800)
def load_tickets():
    df = fetch_hs("""
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
    """)
    return df

# ── HubSpot NPS ───────────────────────────────────────────────
@st.cache_data(ttl=1800)
def load_nps():
    df = fetch_hs("""
        SELECT
            id,
            hs_value                                      AS score,
            hs_response_group                             AS groep,
            hs_survey_type                                AS survey_type,
            would_you_recommend_our_services_to_others_  AS score_fallback,
            createdat                                     AS ingevuld_op
        FROM hubspot_v2.feedback_submissions
    """)
    return df

@st.cache_data(ttl=1800)
def load_cargosnap_schade():
    """Damage Rate via Cargosnap · cargosnap.uploads"""
    df = fetch_hs("""
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
    """)
    return df

@st.cache_data(ttl=3600)
def load_cashweb_mutaties():
    """
    Grootboekmutaties AWC (alaw) · cashweb.ledger_mutations
    debit_credit: 'D' = debet · 'C' = credit
    """
    df = fetch_hs("""
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
    """)
    return df

@st.cache_data(ttl=3600)
def load_cashweb_saldi():
    """Periodesaldi per rekening AWC (alaw) · cashweb.ledger_balances"""
    df = fetch_hs("""
        SELECT
            lb.book_year                                    AS boekjaar,
            lb.account_number                               AS rekeningnummer,
            lb.description                                  AS omschrijving,
            lb.exploitation_code                            AS exploitatie_code,
            lb.sub_administration                           AS subadministratie,
            lb.admin_code                                   AS admin_code,
            CAST(REPLACE(lb.period_amounts_debit,  ',', '.') AS NUMERIC(18,2)) AS periode_debet,
            CAST(REPLACE(lb.period_amounts_credit, ',', '.') AS NUMERIC(18,2)) AS periode_credit,
            CAST(REPLACE(lb.period_amounts_result, ',', '.') AS NUMERIC(18,2)) AS periode_resultaat
        FROM cashweb.ledger_balances AS lb
        WHERE lb.admin_code = 'alaw'
    """)
    return df


# ════════════════════════════════════════════════════════════
# TAB 0 — SAMENVATTING
# Overzicht van alle AWC KPIs op één pagina
# ════════════════════════════════════════════════════════════
with tab_samen:
    st.markdown('<div class="kpi-badge orange">Samenvatting</div>', unsafe_allow_html=True)
    st.subheader("AWC Warehouse KPI Overzicht")
    st.caption("Alle operationele KPI's in één oogopslag · bronnen: 7T Software & HubSpot")

    # ── Bezettingsgraad ──
    try:
        df_tot, df_bez = load_bezetting()
        if not df_tot.empty:
            totaal_pp = int(df_tot["palletplaatsen"].sum())
            bezet_ids = set(df_bez["locatie_id"].tolist()) if not df_bez.empty else set()
            bezette_pp = int(df_tot[df_tot["locatie_id"].isin(bezet_ids)]["palletplaatsen"].sum())
            bez_pct = round((bezette_pp / totaal_pp * 100), 1) if totaal_pp > 0 else 0
        else:
            totaal_pp = bezette_pp = bez_pct = None
    except Exception:
        totaal_pp = bezette_pp = bez_pct = None

    # ── Gemiddelde Doorlooptijd ──
    try:
        df_ontv = load_ontvangsten()
        if not df_ontv.empty:
            df_ontv["ontvangst_datum"] = pd.to_datetime(df_ontv["ontvangst_datum"], errors="coerce")
            df_ontv["mutatie_datum"]   = pd.to_datetime(df_ontv["mutatie_datum"],   errors="coerce")
            df_d = df_ontv[df_ontv["definitief"] == 1].copy()
            df_d["doorlooptijd_d"] = (df_d["mutatie_datum"] - df_d["ontvangst_datum"]).dt.days
            df_d_p = df_d[
                (df_d["ontvangst_datum"] >= ts(start_dt)) &
                (df_d["ontvangst_datum"] <  ts(eind_dt)) &
                (df_d["doorlooptijd_d"]  >= 0)
            ]
            gem_doorlooptijd = round(df_d_p["doorlooptijd_d"].mean(), 1) if not df_d_p.empty else None
            inbound_n = len(df_ontv[
                (df_ontv["ontvangst_datum"] >= ts(start_dt)) &
                (df_ontv["ontvangst_datum"] <  ts(eind_dt))
            ])
        else:
            gem_doorlooptijd = inbound_n = None
    except Exception:
        gem_doorlooptijd = inbound_n = None

    # ── Inventory Accuracy ──
    try:
        df_tel = load_tellingen()
        if not df_tel.empty:
            df_tel["teldatum"] = pd.to_datetime(df_tel["teldatum"], errors="coerce")
            df_tel_p = df_tel[
                (df_tel["teldatum"] >= ts(start_dt)) &
                (df_tel["teldatum"] <  ts(eind_dt))
            ]
            if not df_tel_p.empty:
                correct = (df_tel_p["correctie"].fillna(0).abs() == 0).sum()
                acc_pct = round(correct / len(df_tel_p) * 100, 1)
            else:
                acc_pct = None
        else:
            acc_pct = None
    except Exception:
        acc_pct = None

    # ── Tickets ──
    try:
        df_t = load_tickets()
        if not df_t.empty:
            df_t["aangemaakt_op"] = pd.to_datetime(df_t["aangemaakt_op"], utc=True, errors="coerce")
            tickets_n = len(df_t[
                (df_t["aangemaakt_op"] >= ts(start_dt)) &
                (df_t["aangemaakt_op"] <  ts(eind_dt))
            ])
        else:
            tickets_n = None
    except Exception:
        tickets_n = None

    # ── Render samenvatting metrics ──
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Bezettingsgraad",
        f"{bez_pct:.0f}%" if bez_pct is not None else ("⏳" if not _7T_BESCHIKBAAR else "—"),
        help="(Bezette palletplaatsen / Totaal) × 100%  ·  Bron: 7T"
    )
    c2.metric(
        "Gem. Doorlooptijd",
        f"{gem_doorlooptijd:.0f} dgn" if gem_doorlooptijd is not None else ("⏳" if not _7T_BESCHIKBAAR else "—"),
        help="Gem. dagen van ontvangstdatum → definitief ingeboekt  ·  Bron: 7T"
    )
    c3.metric(
        "Inbound (periode)",
        f"{inbound_n}" if inbound_n is not None else ("⏳" if not _7T_BESCHIKBAAR else "—"),
        help="Aantal ontvangsten in geselecteerde periode  ·  Bron: 7T"
    )
    c4.metric(
        "Inventory Accuracy",
        f"{acc_pct:.0f}%" if acc_pct is not None else ("⏳" if not _7T_BESCHIKBAAR else "—"),
        help="% tellocaties zonder voorraadverschil  ·  Bron: 7T"
    )
    c5.metric(
        "# Tickets",
        f"{tickets_n}" if tickets_n is not None else "—",
        help="Aangemaakt in geselecteerde periode  ·  Bron: HubSpot"
    )

    if not _7T_BESCHIKBAAR:
        st.caption(
            "⏳ **7T Software nog niet gekoppeld** — bezettingsgraad, doorlooptijd, "
            "inbound en inventory accuracy verschijnen automatisch zodra `db_7t` "
            "actief is in Peliqan."
        )

    st.divider()
    st.markdown("#### AWC KPI Structuur — Overzicht databronnen")
    kpi_overzicht = pd.DataFrame([
        # Operationeel
        {"Niveau": "Operationeel", "KPI": "Bezettingsgraad",                   "Bron": "7T Software", "Status": "✅ Actief"},
        {"Niveau": "Operationeel", "KPI": "Storage Lead Time",                 "Bron": "7T Software", "Status": "✅ Actief"},
        {"Niveau": "Operationeel", "KPI": "Dock-to-Stock",                     "Bron": "7T Software", "Status": "✅ Actief"},
        {"Niveau": "Operationeel", "KPI": "Inventory Accuracy",                "Bron": "7T Software", "Status": "✅ Actief"},
        {"Niveau": "Operationeel", "KPI": "OTIF (On-Time In-Full)",            "Bron": "7T Software", "Status": "✅ Actief"},
        {"Niveau": "Operationeel", "KPI": "Inbound Throughput",                "Bron": "7T Software", "Status": "✅ Actief"},
        {"Niveau": "Operationeel", "KPI": "# Tickets (CS)",                    "Bron": "HubSpot",     "Status": "✅ Actief"},
        # Tactisch
        {"Niveau": "Tactisch",     "KPI": "NPS (Net Promoter Score)",          "Bron": "HubSpot",     "Status": "⚙️ Vereist NPS survey"},
        {"Niveau": "Tactisch",     "KPI": "Intern vs. Extern",                 "Bron": "Hooray",      "Status": "🔜 Nog te koppelen"},
        {"Niveau": "Tactisch",     "KPI": "eNPS (Employee NPS)",               "Bron": "Microsoft Forms", "Status": "🔜 Nog te koppelen"},
        # Strategisch
        {"Niveau": "Strategisch",  "KPI": "Bruto Margin per FTE",              "Bron": "Cashweb",     "Status": "🔜 Nog te koppelen"},
        # AWC-specifiek
        {"Niveau": "AWC-specifiek","KPI": "Perfect Order Rate (POR)",          "Bron": "7T Software", "Status": "⚙️ Manco-koppeling nodig"},
        {"Niveau": "AWC-specifiek","KPI": "First Time Right (FTR)",            "Bron": "7T / HubSpot","Status": "⚙️ Definitie verfijnen"},
        {"Niveau": "AWC-specifiek","KPI": "Throughput (in + uit)",             "Bron": "7T + Cargosnap","Status": "⚙️ Outbound bron bevestigen"},
        {"Niveau": "AWC-specifiek","KPI": "Damage Rate",                       "Bron": "7T mutaties", "Status": "🔜 Nog in te richten"},
        {"Niveau": "AWC-specifiek","KPI": "Master Data Accuracy",              "Bron": "7T Software", "Status": "🔜 Definitie nodig"},
    ])
    st.dataframe(kpi_overzicht, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# TAB 1 — BEZETTINGSGRAAD
# KPI: Occupancy Rate %
# Formule: (Bezette palletplaatsen / Totale palletplaatsen) × 100%
# Bron: 7T · Magazijn_Plaatscodes × Magazijn_Plaatssoorten
#            Artikel_Magazijnlocaties (Technische_Voorraad > 0)
# ════════════════════════════════════════════════════════════
with tab_bezet:
    st.markdown('<div class="kpi-badge">Operationeel</div>', unsafe_allow_html=True)
    st.subheader("Bezettingsgraad — Occupancy Rate")
    st.caption(
        "Percentage bezette palletplaatsen · "
        "Bron: 7T · `Magazijn_Plaatscodes` × `Artikel_Magazijnlocaties`"
        " <span class='src-pill src-7t'>7T</span>",
        unsafe_allow_html=True,
    )

    try:
        df_tot, df_bez = load_bezetting()

        if df_tot.empty:
            if not _7T_BESCHIKBAAR:
                _7t_placeholder()
            else:
                st.warning("⚠️ Geen locatiedata beschikbaar. Controleer de 7T warehouse-koppeling.")
        else:
            # Totaal palletplaatsen (excl. geblokkeerde)
            df_actief   = df_tot[df_tot["geblokkeerd"] != 1]
            totaal_pp   = int(df_actief["palletplaatsen"].sum())
            totaal_loc  = len(df_actief)

            # Bezette locaties
            if not df_bez.empty:
                df_bez_merge = df_actief.merge(df_bez, on="locatie_id", how="left")
                df_bezet_loc = df_bez_merge[df_bez_merge["voorraad_totaal"] > 0]
                bezette_pp   = int(df_bezet_loc["palletplaatsen"].sum())
                bezette_loc  = len(df_bezet_loc)
            else:
                bezette_pp  = bezette_loc = 0

            vrije_pp  = totaal_pp  - bezette_pp
            bez_pct   = round((bezette_pp  / totaal_pp  * 100), 1) if totaal_pp  > 0 else 0
            vrij_pct  = round((vrije_pp    / totaal_pp  * 100), 1) if totaal_pp  > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Bezettingsgraad",         f"{bez_pct:.1f}%")
            c2.metric("Bezette palletplaatsen",  f"{bezette_pp:,}")
            c3.metric("Vrije palletplaatsen",    f"{vrije_pp:,}")
            c4.metric("Totaal palletplaatsen",   f"{totaal_pp:,}")

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("📊 Bezetting per magazijn")
                if "magazijn_id" in df_actief.columns:
                    df_mag = df_actief.copy()
                    df_mag["bezet"] = df_mag["locatie_id"].isin(
                        df_bezet_loc["locatie_id"].tolist() if not df_bez.empty else []
                    )
                    mag_grp = df_mag.groupby("magazijn_id").agg(
                        Totaal_PP=("palletplaatsen", "sum"),
                        Bezet_PP=("palletplaatsen", lambda x: x[df_mag.loc[x.index, "bezet"]].sum()),
                    ).reset_index()
                    mag_grp["Bezettingsgraad %"] = (
                        mag_grp["Bezet_PP"] / mag_grp["Totaal_PP"] * 100
                    ).round(1)
                    mag_grp.columns = ["Magazijn ID", "Totaal PP", "Bezet PP", "Bezettingsgraad %"]
                    st.dataframe(mag_grp.sort_values("Bezettingsgraad %", ascending=False),
                                 use_container_width=True, hide_index=True)

            with col_b:
                st.subheader("🗺 Bezetting vs. Vrij")
                df_bar = pd.DataFrame({
                    "Status": ["Bezet", "Vrij"],
                    "Palletplaatsen": [bezette_pp, vrije_pp],
                    "Percentage": [bez_pct, vrij_pct],
                })
                st.bar_chart(df_bar.set_index("Status")["Palletplaatsen"], use_container_width=True)

            st.divider()
            st.subheader("📋 Locatie-detail (top 50 bezette locaties)")
            if not df_bez.empty:
                df_detail = df_actief.merge(df_bez, on="locatie_id", how="inner").sort_values(
                    "voorraad_totaal", ascending=False
                ).head(50)
                st.dataframe(
                    df_detail[["locatienaam", "palletplaatsen", "artikel_partijen", "voorraad_totaal"]]
                    .rename(columns={
                        "locatienaam":     "Locatie",
                        "palletplaatsen":  "Pallet plaatsen",
                        "artikel_partijen":"Artikel partijen",
                        "voorraad_totaal": "Technische voorraad",
                    }),
                    use_container_width=True, hide_index=True,
                )

    except Exception as e:
        st.error(f"⚠️ Fout bij laden bezettingsdata: {e}")
        st.info(
            "Controleer of de 7T Software koppeling actief is in Peliqan "
            f"(warehouse-naam: `{WAREHOUSE_7T}`)."
        )

    with st.expander("ℹ️ Toelichting"):
        st.markdown("""
        **Bezettingsgraad** = `(Bezette palletplaatsen / Totale palletplaatsen) × 100%`

        | Tabel | Gebruik |
        |-------|---------|
        | `Magazijn_Plaatscodes` | Alle actieve locaties + `Magazijn_Plaatssoort_ID` |
        | `Magazijn_Plaatssoorten` | `Aantal_Palletplaatsen` per locatietype |
        | `Artikel_Magazijnlocaties` | Locaties met `Technische_Voorraad > 0` = bezet |

        Geblokkeerde locaties (`Geblokkeerd_Voor_Picken = 1`) en externe locaties (`Extern = 1`)
        worden buiten beschouwing gelaten.
        """)


# ════════════════════════════════════════════════════════════
# TAB 2 — DOORLOOPTIJD / DOCK-TO-STOCK
# KPI 1: Storage Lead Time — gem. dagen ontvangst → ingeruimd
# KPI 2: Dock-to-Stock     — aankomst leverancier → eerste opslag
# Bron: 7T · Ontvangsten
# ════════════════════════════════════════════════════════════
with tab_lead:
    st.markdown('<div class="kpi-badge">Operationeel</div>', unsafe_allow_html=True)
    st.subheader("Storage Lead Time & Dock-to-Stock")
    st.caption(
        "Gemiddelde doorlooptijd in- en opslag · "
        "Bron: 7T · `Ontvangsten`"
        " <span class='src-pill src-7t'>7T</span>",
        unsafe_allow_html=True,
    )

    try:
        df_ontv = load_ontvangsten()

        if df_ontv.empty:
            _7t_placeholder() if not _7T_BESCHIKBAAR else st.warning("⚠️ Geen ontvangstdata in 7T.")
        else:
            df_ontv["ontvangst_datum"]      = pd.to_datetime(df_ontv["ontvangst_datum"],      errors="coerce")
            df_ontv["aankomst_leverancier"] = pd.to_datetime(df_ontv["aankomst_leverancier"], errors="coerce")
            df_ontv["mutatie_datum"]        = pd.to_datetime(df_ontv["mutatie_datum"],        errors="coerce")

            # Storage Lead Time: ontvangst_datum → mutatie_datum (definitief=1)
            df_def  = df_ontv[df_ontv["definitief"] == 1].copy()
            df_def["storage_lead_days"] = (
                df_def["mutatie_datum"] - df_def["ontvangst_datum"]
            ).dt.days.clip(lower=0)

            # Dock-to-Stock: aankomst_leverancier → ontvangst_datum (als proxy voor inruiming)
            df_d2s = df_ontv[df_ontv["aankomst_leverancier"].notna()].copy()
            df_d2s["dock_to_stock_days"] = (
                df_d2s["ontvangst_datum"] - df_d2s["aankomst_leverancier"]
            ).dt.days.clip(lower=0)

            # Filter op periode
            mask_h = (df_def["ontvangst_datum"] >= ts(start_dt)) & (df_def["ontvangst_datum"] < ts(eind_dt))
            mask_v = (df_def["ontvangst_datum"] >= ts(vorige_start)) & (df_def["ontvangst_datum"] < ts(vorige_eind))
            df_slt_h = df_def[mask_h]
            df_slt_v = df_def[mask_v]

            mask_d2s_h = (df_d2s["ontvangst_datum"] >= ts(start_dt)) & (df_d2s["ontvangst_datum"] < ts(eind_dt))
            mask_d2s_v = (df_d2s["ontvangst_datum"] >= ts(vorige_start)) & (df_d2s["ontvangst_datum"] < ts(vorige_eind))
            df_d2s_h   = df_d2s[mask_d2s_h]
            df_d2s_v   = df_d2s[mask_d2s_v]

            slt_gem_h  = round(df_slt_h["storage_lead_days"].mean(), 1) if not df_slt_h.empty else None
            slt_gem_v  = round(df_slt_v["storage_lead_days"].mean(), 1) if not df_slt_v.empty else None
            slt_med_h  = round(df_slt_h["storage_lead_days"].median(), 1) if not df_slt_h.empty else None
            d2s_gem_h  = round(df_d2s_h["dock_to_stock_days"].mean(), 1) if not df_d2s_h.empty else None
            d2s_gem_v  = round(df_d2s_v["dock_to_stock_days"].mean(), 1) if not df_d2s_v.empty else None

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gem. Storage Lead Time",
                      f"{slt_gem_h:.1f} dgn" if slt_gem_h is not None else "—",
                      delta_tekst(slt_gem_h or 0, slt_gem_v or 0))
            c2.metric("Mediaan Lead Time",
                      f"{slt_med_h:.1f} dgn" if slt_med_h is not None else "—")
            c3.metric("Gem. Dock-to-Stock",
                      f"{d2s_gem_h:.1f} dgn" if d2s_gem_h is not None else "—",
                      delta_tekst(d2s_gem_h or 0, d2s_gem_v or 0))
            c4.metric("Ontvangsten definitief (periode)",
                      f"{len(df_slt_h)}")

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("📈 Storage Lead Time — trend")
                if not df_slt_h.empty:
                    df_tr = (
                        df_slt_h.set_index("ontvangst_datum")["storage_lead_days"]
                        .resample(freq).mean().dropna().reset_index()
                    )
                    df_tr.columns = ["Periode", "Gem. lead days"]
                    st.line_chart(df_tr, x="Periode", y="Gem. lead days", use_container_width=True)
                else:
                    st.info("Geen definitief ingeboekte ontvangsten in de periode.")

            with col_b:
                st.subheader("📊 Verdeling doorlooptijd (dagen)")
                if not df_slt_h.empty:
                    bins = [0, 1, 2, 3, 5, 7, 14, 30, 999]
                    labels = ["0d", "1d", "2d", "3-4d", "5-6d", "7-13d", "14-29d", "30+d"]
                    df_slt_h["bucket"] = pd.cut(
                        df_slt_h["storage_lead_days"], bins=bins, labels=labels, right=False
                    )
                    hist = df_slt_h["bucket"].value_counts().sort_index().reset_index()
                    hist.columns = ["Doorlooptijd", "Aantal ontvangsten"]
                    st.bar_chart(hist.set_index("Doorlooptijd"), use_container_width=True)

            st.divider()
            st.subheader("📋 Ontvangsten met langste doorlooptijd (top 20)")
            if not df_slt_h.empty:
                top20 = df_slt_h.nlargest(20, "storage_lead_days")[
                    ["ontvangst_id", "ontvangst_datum", "storage_lead_days", "klant_id", "status"]
                ].rename(columns={
                    "ontvangst_id":        "Ontvangst ID",
                    "ontvangst_datum":     "Ontvangstdatum",
                    "storage_lead_days":   "Lead Time (dgn)",
                    "klant_id":            "Klant ID",
                    "status":              "Status",
                })
                st.dataframe(top20, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"⚠️ Fout bij laden doorlooptijddata: {e}")

    with st.expander("ℹ️ Toelichting"):
        st.markdown("""
        **Storage Lead Time** = gem. dagen van `Ontvangsten.Datum` tot `Ontvangsten.MutatieDatum`
        (alleen records waarbij `Ontvangst_Definitief = 1`, d.w.z. volledig verwerkt).

        **Dock-to-Stock** = gem. dagen van `Aankomst_Leverancier` tot `Ontvangsten.Datum`
        (als proxy voor de tijd tussen aankomst chauffeur en formele ontvangstregistratie).

        Voor een exactere dock-to-stock meting kan de `Ontvangstregel_Partijen.Houdbaarheidsdatum`
        of de `Inruim_Gebr_ID`-timestamp worden ingezet zodra dat veld consequent gevuld is.
        """)


# ════════════════════════════════════════════════════════════
# TAB 3 — DOORVOER / THROUGHPUT
# KPI: Inbound doorvoer (# ontvangsten per periode)
#       Uitgesplitst per week / per administratie
# Bron: 7T · Ontvangsten
# ════════════════════════════════════════════════════════════
with tab_door:
    st.markdown('<div class="kpi-badge">Operationeel</div>', unsafe_allow_html=True)
    st.subheader("Doorvoer — Throughput")
    st.caption(
        "Totale doorvoer van goederen door het warehouse · "
        "Bron: 7T · `Ontvangsten`"
        " <span class='src-pill src-7t'>7T</span>",
        unsafe_allow_html=True,
    )

    try:
        df_ontv = load_ontvangsten()

        if df_ontv.empty:
            _7t_placeholder() if not _7T_BESCHIKBAAR else st.warning("⚠️ Geen ontvangstdata beschikbaar.")
        else:
            df_ontv["ontvangst_datum"] = pd.to_datetime(df_ontv["ontvangst_datum"], errors="coerce")

            df_inb_h = df_ontv[
                (df_ontv["ontvangst_datum"] >= ts(start_dt)) &
                (df_ontv["ontvangst_datum"] <  ts(eind_dt))
            ]
            df_inb_v = df_ontv[
                (df_ontv["ontvangst_datum"] >= ts(vorige_start)) &
                (df_ontv["ontvangst_datum"] <  ts(vorige_eind))
            ]
            df_def_h = df_inb_h[df_inb_h["definitief"] == 1]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Inbound ontvangsten",
                      len(df_inb_h),
                      delta_tekst(len(df_inb_h), len(df_inb_v)))
            c2.metric("Definitief verwerkt",
                      len(df_def_h))
            c3.metric("In verwerking",
                      len(df_inb_h) - len(df_def_h))
            c4.metric("Vorige periode",
                      len(df_inb_v))

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("📈 Inbound trend")
                if not df_inb_h.empty:
                    df_tr = (
                        df_inb_h.set_index("ontvangst_datum").resample(freq).size()
                        .reset_index(name="Ontvangsten")
                    )
                    df_tr.columns = ["Periode", "Ontvangsten"]
                    st.bar_chart(df_tr, x="Periode", y="Ontvangsten", use_container_width=True)
                else:
                    st.info("Geen ontvangsten in de geselecteerde periode.")

            with col_b:
                st.subheader("📊 Per administratie (entiteit)")
                if not df_inb_h.empty and "administratie_id" in df_inb_h.columns:
                    adm = df_inb_h.groupby("administratie_id").size().reset_index(name="Aantal")
                    adm.columns = ["Administratie ID", "Aantal ontvangsten"]
                    st.dataframe(adm.sort_values("Aantal ontvangsten", ascending=False),
                                 use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("📋 Verwerkingsstatus — huidige periode")
            if not df_inb_h.empty:
                status_tbl = df_inb_h["status"].value_counts().reset_index()
                status_tbl.columns = ["Status (7T code)", "Aantal"]
                status_map = {
                    "10": "Aangemeld",
                    "20": "In ontvangst",
                    "30": "Ontvangen",
                    "40": "Ingeboekt",
                    "50": "Definitief",
                }
                status_tbl["Omschrijving"] = status_tbl["Status (7T code)"].astype(str).map(
                    status_map
                ).fillna("Onbekend")
                st.dataframe(status_tbl[["Status (7T code)", "Omschrijving", "Aantal"]],
                             use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"⚠️ Fout bij laden doorvoerdata: {e}")

    with st.expander("ℹ️ Toelichting"):
        st.markdown("""
        **Throughput inbound** = `COUNT(Ontvangsten.ID)` per periode.

        Voor outbound throughput (picken + verzenden) zijn de `Logorder_Combinaties` en
        `LogOrder_Afleverdata`-tabellen de aangewezen bron. Dit vereist bevestiging
        van het correcte status-veld voor "afgeleverd".

        Koppeling met **Cargosnap** is aanbevolen voor een end-to-end meting
        (aankomst container → laatste scan bij uitlevering).
        """)


# ════════════════════════════════════════════════════════════
# TAB 4 — KWALITEIT
# KPI 1: Inventory Accuracy — telling verwacht vs. geteld
# KPI 2: OTIF — orderregels op tijd / verschoven leverdatum
# KPI 3: (indicator) Dock-to-stock afwijkingen
# Bron: 7T · Telling_Locaties · Orderregel_Leverdata
# ════════════════════════════════════════════════════════════
with tab_kwal:
    st.markdown('<div class="kpi-badge">Kwaliteit</div>', unsafe_allow_html=True)
    st.subheader("Kwaliteit — Inventory Accuracy & OTIF")
    st.caption(
        "Voorraadnauwkeurigheid + leverbetrouwbaarheid · "
        "Bron: 7T · `Telling_Locaties` · `Orderregel_Leverdata`"
        " <span class='src-pill src-7t'>7T</span>",
        unsafe_allow_html=True,
    )

    # ── Inventory Accuracy ──
    try:
        df_tel = load_tellingen()

        if not df_tel.empty:
            df_tel["teldatum"] = pd.to_datetime(df_tel["teldatum"], errors="coerce")
            df_tel_h = df_tel[
                (df_tel["teldatum"] >= ts(start_dt)) &
                (df_tel["teldatum"] <  ts(eind_dt))
            ]
            df_tel_v = df_tel[
                (df_tel["teldatum"] >= ts(vorige_start)) &
                (df_tel["teldatum"] <  ts(vorige_eind))
            ]

            def calc_acc(df):
                if df.empty:
                    return None, None
                df = df.copy()
                df["correctie_abs"] = df["correctie"].fillna(0).abs()
                correct_n = (df["correctie_abs"] == 0).sum()
                return round(correct_n / len(df) * 100, 1), len(df)

            acc_h, n_h = calc_acc(df_tel_h)
            acc_v, n_v = calc_acc(df_tel_v)

        else:
            acc_h = acc_v = n_h = n_v = None
            df_tel_h = pd.DataFrame()
    except Exception as e:
        acc_h = acc_v = n_h = n_v = None
        df_tel_h = pd.DataFrame()
        st.warning(f"Teldata niet beschikbaar: {e}")

    # ── OTIF ──
    try:
        df_ld = load_leverdata()
        if not df_ld.empty:
            df_ld["mutatie_datum"] = pd.to_datetime(df_ld["mutatie_datum"], errors="coerce")
            df_ld["gepland"]       = pd.to_datetime(df_ld["gepland"],       errors="coerce")
            df_ld["werkelijk"]     = pd.to_datetime(df_ld["werkelijk"],     errors="coerce")

            df_ld_h = df_ld[
                (df_ld["mutatie_datum"] >= ts(start_dt)) &
                (df_ld["mutatie_datum"] <  ts(eind_dt)) &
                (df_ld["informatief"] == 0)  # alleen formele wijzigingen
            ]
            df_ld_v = df_ld[
                (df_ld["mutatie_datum"] >= ts(vorige_start)) &
                (df_ld["mutatie_datum"] <  ts(vorige_eind)) &
                (df_ld["informatief"] == 0)
            ]

            def calc_otif(df_base, df_wijz):
                """
                OTIF-proxy: orderregels ZONDER leverdatum-wijziging = on time.
                Verhouding: (totaal orderregels - gewijzigde) / totaal orderregels.
                """
                if df_base.empty:
                    return None, None, None
                gewijzigd_n   = len(df_wijz)
                # Benadering: totaal verschoven als proxy voor "te laat"
                verschoven_n  = len(df_wijz[df_wijz["werkelijk"] > df_wijz["gepland"]])
                on_time_proxy = max(0, len(df_base) - verschoven_n)
                otif_pct      = round(on_time_proxy / len(df_base) * 100, 1) if df_base else None
                return otif_pct, verschoven_n, len(df_base)

            otif_h, versch_h, total_h = calc_otif(df_ld_h, df_ld_h[df_ld_h["werkelijk"].notna()])
            otif_v, versch_v, total_v = calc_otif(df_ld_v, df_ld_v[df_ld_v["werkelijk"].notna()])
        else:
            otif_h = otif_v = versch_h = total_h = None
            df_ld_h = pd.DataFrame()
    except Exception as e:
        otif_h = otif_v = versch_h = total_h = None
        df_ld_h = pd.DataFrame()
        st.warning(f"OTIF-data niet beschikbaar: {e}")

    # ── Render metrics ──
    st.subheader("Inventory Accuracy")
    c1, c2, c3 = st.columns(3)
    c1.metric("Inventory Accuracy",
              f"{acc_h:.1f}%" if acc_h is not None else "—",
              delta_tekst(acc_h or 0, acc_v or 0))
    c2.metric("Getelde locaties (periode)",
              f"{n_h}" if n_h is not None else "—")
    c3.metric("Vorige periode",
              f"{acc_v:.1f}%" if acc_v is not None else "—")

    if not df_tel_h.empty:
        df_tel_h["correctie_abs"] = df_tel_h["correctie"].fillna(0).abs()
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📈 Accuracy trend")
            df_acc_tr = (
                df_tel_h.set_index("teldatum")
                .resample(freq)
                .apply(lambda g: round((g["correctie_abs"] == 0).sum() / max(len(g), 1) * 100, 1))
                .reset_index()
            )
            df_acc_tr.columns = ["Periode", "Accuracy %"]
            st.line_chart(df_acc_tr, x="Periode", y="Accuracy %", use_container_width=True)
        with col_b:
            st.subheader("📋 Locaties met verschil")
            df_fout = df_tel_h[df_tel_h["correctie_abs"] > 0].sort_values(
                "correctie_abs", ascending=False
            ).head(20)
            if not df_fout.empty:
                st.dataframe(
                    df_fout[["telling_locatie_id", "telling_id", "verwacht", "geteld", "correctie_abs"]]
                    .rename(columns={
                        "telling_locatie_id": "Locatie ID",
                        "telling_id":         "Telling ID",
                        "verwacht":           "Verwacht",
                        "geteld":             "Geteld",
                        "correctie_abs":      "|Correctie|",
                    }),
                    use_container_width=True, hide_index=True,
                )
            else:
                st.success("✅ Geen correcties bij getelde locaties in deze periode.")

    st.divider()
    st.subheader("OTIF — On-Time In-Full (proxy)")
    c1, c2, c3 = st.columns(3)
    c1.metric("OTIF %",
              f"{otif_h:.1f}%" if otif_h is not None else "—",
              delta_tekst(otif_h or 0, otif_v or 0))
    c2.metric("Verschoven leverdata",
              f"{versch_h}" if versch_h is not None else "—")
    c3.metric("Totaal orderregels (mutaties)",
              f"{total_h}" if total_h is not None else "—")

    if not df_ld_h.empty:
        df_ld_h["vertraging_d"] = (
            df_ld_h["werkelijk"] - df_ld_h["gepland"]
        ).dt.days
        df_vertraagd = df_ld_h[df_ld_h["vertraging_d"] > 0].copy()
        if not df_vertraagd.empty:
            st.subheader("📋 Meest vertraagde orderregels (top 20)")
            st.dataframe(
                df_vertraagd.nlargest(20, "vertraging_d")[
                    ["orderregel_id", "gepland", "werkelijk", "vertraging_d"]
                ].rename(columns={
                    "orderregel_id": "Orderregel ID",
                    "gepland":       "Geplande leverdatum",
                    "werkelijk":     "Nieuwe leverdatum",
                    "vertraging_d":  "Vertraging (dgn)",
                }),
                use_container_width=True, hide_index=True,
            )

    if otif_h is None and acc_h is None:
        if not _7T_BESCHIKBAAR:
            _7t_placeholder()
        else:
            st.info(f"ℹ️ 7T-koppeling niet beschikbaar. Controleer warehouse `{WAREHOUSE_7T}` in Peliqan.")

    st.divider()
    st.subheader("📸 Damage Rate — Cargosnap")
    st.caption("% scans met schade · Bron: `cargosnap.uploads` <span class='src-pill src-hs'>Cargosnap</span>", unsafe_allow_html=True)

    try:
        df_cs = load_cargosnap_schade()
        if df_cs.empty:
            st.info("Geen Cargosnap-data beschikbaar.")
        else:
            df_cs["created_at"] = pd.to_datetime(df_cs["created_at"], utc=True, errors="coerce")
            df_cs_h = df_cs[(df_cs["created_at"] >= ts(start_dt)) & (df_cs["created_at"] < ts(eind_dt))]
            df_cs_v = df_cs[(df_cs["created_at"] >= ts(vorige_start)) & (df_cs["created_at"] < ts(vorige_eind))]

            def damage_rate(df):
                if df.empty: return None, None, None
                totaal = len(df)
                schade = df["has_damage"].fillna(False).astype(bool).sum()
                pct    = round(schade / totaal * 100, 2) if totaal > 0 else 0
                return pct, int(schade), totaal

            dr_h, sch_h, tot_h = damage_rate(df_cs_h)
            dr_v, sch_v, tot_v = damage_rate(df_cs_v)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Damage Rate",      f"{dr_h:.2f}%" if dr_h is not None else "—",
                      delta_tekst(dr_h or 0, dr_v or 0))
            c2.metric("Scans met schade", f"{sch_h}" if sch_h is not None else "—")
            c3.metric("Totaal scans",     f"{tot_h}" if tot_h is not None else "—")
            c4.metric("Vorige periode",   f"{dr_v:.2f}%" if dr_v is not None else "—")

            if sch_h and sch_h > 0:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("📊 Schade per type")
                    schade_type = (
                        df_cs_h[df_cs_h["has_damage"] == True]["schade_type"]
                        .fillna("Onbekend").value_counts().reset_index()
                    )
                    schade_type.columns = ["Schade type", "Aantal"]
                    st.dataframe(schade_type, use_container_width=True, hide_index=True)
                with col_b:
                    st.subheader("📈 Damage Rate trend")
                    df_dr_tr = (
                        df_cs_h.set_index("created_at")
                        .resample(freq)
                        .apply(lambda g: round(
                            g["has_damage"].fillna(False).astype(bool).sum() / max(len(g), 1) * 100, 2
                        ))
                        .reset_index()
                    )
                    df_dr_tr.columns = ["Periode", "Damage Rate %"]
                    st.line_chart(df_dr_tr, x="Periode", y="Damage Rate %", use_container_width=True)

    except Exception as e:
        st.warning(f"Cargosnap-data niet beschikbaar: {e}")

    with st.expander("ℹ️ Toelichting"):
        st.markdown("""
        **Inventory Accuracy** = `(locaties zonder correctie / totaal getelde locaties) × 100%`
        Bron: `Telling_Locaties` — alleen afgeronde tellingen (`Telling_Gereed = 1`).

        **OTIF (proxy)** = orderregels waarbij `Orderregel_Leverdata.Nieuwe_Leverdatum`
        ≤ `Oude_Leverdatum` (of geen wijziging). Dit is een proxy; voor exacte OTIF
        is koppeling met scantijdstip bij uitlevering nodig.

        **Damage Rate** = `(scans met has_damage = true / totaal scans) × 100%`
        Bron: `cargosnap.uploads` — live beschikbaar.

        **Geplande vervolgstap:** `Logorder_Combinaties` + `LogOrder_Afleverdata`
        bevatten de werkelijke levermomenten voor een nauwkeurigere OTIF-berekening.
        """)


# ════════════════════════════════════════════════════════════
# TAB 5 — TICKETS (HubSpot)
# KPI: # tickets per periode + trendlijn
# ════════════════════════════════════════════════════════════
with tab_ticks:
    st.markdown('<div class="kpi-badge">Customer Service</div>', unsafe_allow_html=True)
    st.subheader("# Tickets (Customer Service)")
    st.caption(
        "Aantal binnengekomen tickets · "
        "Bron: HubSpot · `tickets`"
        " <span class='src-pill src-hs'>HubSpot</span>",
        unsafe_allow_html=True,
    )

    try:
        df_t = load_tickets()

        if df_t.empty:
            st.warning("⚠️ Geen ticketdata in HubSpot.")
        else:
            df_t["aangemaakt_op"] = pd.to_datetime(df_t["aangemaakt_op"], utc=True, errors="coerce")
            df_t["gesloten_op"]   = pd.to_datetime(df_t["gesloten_op"],   utc=True, errors="coerce")

            df_t_h = df_t[(df_t["aangemaakt_op"] >= ts(start_dt)) & (df_t["aangemaakt_op"] < ts(eind_dt))]
            df_t_v = df_t[(df_t["aangemaakt_op"] >= ts(vorige_start)) & (df_t["aangemaakt_op"] < ts(vorige_eind))]

            open_n   = len(df_t_h[df_t_h["gesloten_op"].isna()])
            closed_n = len(df_t_h[df_t_h["gesloten_op"].notna()])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tickets (periode)",
                      len(df_t_h),
                      delta_tekst(len(df_t_h), len(df_t_v)))
            c2.metric("Open",     open_n)
            c3.metric("Gesloten", closed_n)
            c4.metric("Vorige periode", len(df_t_v))

            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("📈 Tickets per periode")
                df_tr = df_t_h.set_index("aangemaakt_op").resample(freq).size().reset_index(name="Tickets")
                df_tr.columns = ["Periode", "Tickets"]
                st.bar_chart(df_tr, x="Periode", y="Tickets", use_container_width=True)
            with col_b:
                st.subheader("📊 Per prioriteit")
                if "prioriteit" in df_t_h.columns:
                    prio = df_t_h["prioriteit"].fillna("Onbekend").value_counts().reset_index()
                    prio.columns = ["Prioriteit", "Aantal"]
                    st.dataframe(prio, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("📋 Ticketoverzicht — huidige periode")
            cols_show = [c for c in ["onderwerp", "categorie", "prioriteit", "status", "aangemaakt_op", "gesloten_op"] if c in df_t_h.columns]
            st.dataframe(
                df_t_h[cols_show].rename(columns={
                    "onderwerp":    "Onderwerp",
                    "categorie":    "Categorie",
                    "prioriteit":   "Prioriteit",
                    "status":       "Status",
                    "aangemaakt_op":"Aangemaakt",
                    "gesloten_op":  "Gesloten op",
                }).sort_values("Aangemaakt", ascending=False).head(50),
                use_container_width=True, hide_index=True,
            )

    except Exception as e:
        st.error(f"⚠️ Fout bij laden tickets: {e}")


# ════════════════════════════════════════════════════════════
# TAB 6 — NPS (HubSpot)
# KPI: Net Promoter Score
# ════════════════════════════════════════════════════════════
with tab_nps:
    st.markdown('<div class="kpi-badge">Tactisch</div>', unsafe_allow_html=True)
    st.subheader("NPS — Net Promoter Score")
    st.caption(
        "% Promoters – % Detractors · "
        "Bron: HubSpot Service Hub · `feedback_submissions`"
        " <span class='src-pill src-hs'>HubSpot</span>",
        unsafe_allow_html=True,
    )

    try:
        df_nps = load_nps()

        if df_nps.empty:
            st.warning(
                "⚠️ Geen NPS-data beschikbaar. "
                "Controleer of HubSpot Service Hub actief is en een NPS-survey geconfigureerd is."
            )
        else:
            df_nps["ingevuld_op"] = pd.to_datetime(df_nps["ingevuld_op"], utc=True, errors="coerce")

            # Score: hs_value → fallback score_fallback
            df_nps["nps_score"] = pd.to_numeric(df_nps["score"], errors="coerce")
            mask_miss = df_nps["nps_score"].isna()
            df_nps.loc[mask_miss, "nps_score"] = pd.to_numeric(
                df_nps.loc[mask_miss, "score_fallback"], errors="coerce"
            )

            df_nps_clean = df_nps[df_nps["nps_score"].notna()].copy()

            def categorize(s):
                if s >= 9:   return "Promoter"
                if s >= 7:   return "Passief"
                return "Detractor"

            df_nps_clean["categorie"] = df_nps_clean["nps_score"].apply(categorize)

            def calc_nps(df):
                n = len(df)
                if n == 0: return None
                p = (df["categorie"] == "Promoter").sum()
                d = (df["categorie"] == "Detractor").sum()
                return round((p - d) / n * 100, 1)

            df_h = df_nps_clean[
                (df_nps_clean["ingevuld_op"] >= ts(start_dt)) &
                (df_nps_clean["ingevuld_op"] <  ts(eind_dt))
            ]
            df_v = df_nps_clean[
                (df_nps_clean["ingevuld_op"] >= ts(vorige_start)) &
                (df_nps_clean["ingevuld_op"] <  ts(vorige_eind))
            ]

            nps_h  = calc_nps(df_h)
            nps_v  = calc_nps(df_v)

            if nps_h is not None:
                p_pct = round((df_h["categorie"] == "Promoter").sum()  / len(df_h) * 100, 1)
                pa_pct= round((df_h["categorie"] == "Passief").sum()   / len(df_h) * 100, 1)
                d_pct = round((df_h["categorie"] == "Detractor").sum() / len(df_h) * 100, 1)

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("NPS Score",     f"{nps_h:+.0f}", delta_tekst(nps_h, nps_v or 0))
                c2.metric("Promoters",     f"{p_pct:.0f}%")
                c3.metric("Passieven",     f"{pa_pct:.0f}%")
                c4.metric("Detractors",    f"{d_pct:.0f}%")
                c5.metric("Responses",     len(df_h))

                st.divider()
                st.subheader("📈 NPS trend")
                if len(df_h) >= 3:
                    df_tr = (
                        df_h.set_index("ingevuld_op")
                        .resample(freq)
                        .apply(calc_nps)
                        .dropna().reset_index()
                    )
                    df_tr.columns = ["Periode", "NPS"]
                    st.line_chart(df_tr, x="Periode", y="NPS", use_container_width=True)
            else:
                st.info("Geen NPS-responses met geldige score in de geselecteerde periode.")
                if "survey_type" in df_nps.columns:
                    st.subheader("Aanwezige survey types")
                    st.dataframe(
                        df_nps["survey_type"].value_counts().reset_index()
                        .rename(columns={"survey_type": "Survey Type", "count": "Aantal"}),
                        use_container_width=True, hide_index=True,
                    )

    except Exception as e:
        st.error(f"⚠️ Fout bij laden NPS-data: {e}")

    with st.expander("ℹ️ Toelichting"):
        st.markdown("""
        **NPS** = `((Promoters − Detractors) / Totaal) × 100`

        | Score | Categorie | Kolom |
        |-------|-----------|-------|
        | 9–10  | Promoter  | `hs_value` |
        | 7–8   | Passief   | `hs_value` |
        | 0–6   | Detractor | `hs_value` |

        Fallback als `hs_value` leeg: `would_you_recommend_our_services_to_others_`
        """)



# ════════════════════════════════════════════════════════════
# TAB 7 — FINANCIEEL (Cashweb · alaw)
# KPI: Omzet, Bruto Marge, Kostenoverzicht
# Bron: dw_2401 · cashweb.ledger_mutations / ledger_balances
#       Gefilterd op admin_code = 'alaw' (Amsterdam Warehouse Company)
# ════════════════════════════════════════════════════════════

with tab_fin:
    st.markdown('<div class="kpi-badge orange">Financieel</div>', unsafe_allow_html=True)
    st.subheader("Financieel Overzicht — Amsterdam Warehouse Company")
    st.caption(
        "Omzet · Kosten · Bruto Marge · Bron: Cashweb (`alaw` administratie) · "
        "`cashweb.ledger_mutations` / `cashweb.ledger_balances`"
        " <span class='src-pill src-hs'>Cashweb</span>",
        unsafe_allow_html=True,
    )

    try:
        df_mut = load_cashweb_mutaties()

        if df_mut.empty:
            st.warning("⚠️ Geen Cashweb-mutaties beschikbaar voor administratie `alaw`.")
        else:
            df_mut["boekdatum"] = pd.to_datetime(df_mut["boekdatum"], errors="coerce")
            df_mut["bedrag"]    = pd.to_numeric(df_mut["bedrag"], errors="coerce").fillna(0)

            df_mut_h = df_mut[
                (df_mut["boekdatum"] >= start_dt) &
                (df_mut["boekdatum"] <  eind_dt)
            ]
            df_mut_v = df_mut[
                (df_mut["boekdatum"] >= vorige_start) &
                (df_mut["boekdatum"] <  vorige_eind)
            ]

            # ── Bepaal exploitatierekeningen via ledger_balances ──
            try:
                df_bal = load_cashweb_saldi()
                exploit_rek = set(
                    df_bal[
                        df_bal["exploitatie_code"].notna() &
                        (df_bal["exploitatie_code"].astype(str).str.strip() != "")
                    ]["rekeningnummer"].astype(str).tolist()
                ) if not df_bal.empty else set()
            except Exception:
                exploit_rek = set()

            def mask_omzet(df):
                if exploit_rek:
                    return df["rekeningnummer"].astype(str).isin(exploit_rek) & (df["dc"] == "C")
                return df["dc"] == "C"   # fallback: alle credits

            def mask_kosten(df):
                if exploit_rek:
                    return df["rekeningnummer"].astype(str).isin(exploit_rek) & (df["dc"] == "D")
                return df["dc"] == "D"   # fallback: alle debets

            omzet_h  = df_mut_h[mask_omzet(df_mut_h)]["bedrag"].sum()
            kosten_h = df_mut_h[mask_kosten(df_mut_h)]["bedrag"].sum()
            omzet_v  = df_mut_v[mask_omzet(df_mut_v)]["bedrag"].sum()
            kosten_v = df_mut_v[mask_kosten(df_mut_v)]["bedrag"].sum()
            marge_h  = omzet_h - kosten_h
            marge_v  = omzet_v - kosten_v
            marge_pct_h = round(marge_h / omzet_h * 100, 1) if omzet_h > 0 else None
            marge_pct_v = round(marge_v / omzet_v * 100, 1) if omzet_v > 0 else None

            bron_label = "exploitatierekeningen" if exploit_rek else "alle credit/debet mutaties (fallback)"

            def eur(x):
                return f"€ {x:,.0f}".replace(",", ".")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Omzet (periode)",  eur(omzet_h),  delta_tekst(omzet_h, omzet_v))
            c2.metric("Kosten (periode)", eur(kosten_h), delta_tekst(kosten_h, kosten_v))
            c3.metric("Bruto Marge",      eur(marge_h),  delta_tekst(marge_h, marge_v))
            c4.metric("Marge %",
                      f"{marge_pct_h:.1f}%" if marge_pct_h is not None else "—",
                      delta_tekst(marge_pct_h or 0, marge_pct_v or 0))
            st.caption(f"ℹ️ Berekend op basis van: {bron_label}")

            st.divider()
            col_a, col_b = st.columns(2)

            with col_a:
                st.subheader("📈 Omzet per periode")
                df_omzet_tr = (
                    df_mut_h[mask_omzet(df_mut_h)]
                    .set_index("boekdatum")["bedrag"]
                    .resample(freq).sum().reset_index()
                )
                df_omzet_tr.columns = ["Periode", "Omzet (€)"]
                if not df_omzet_tr.empty and df_omzet_tr["Omzet (€)"].sum() > 0:
                    st.bar_chart(df_omzet_tr, x="Periode", y="Omzet (€)", use_container_width=True)
                else:
                    st.info("Geen omzetmutaties in de periode.")

            with col_b:
                st.subheader("📊 Kosten per dagboek")
                df_kost_dag = (
                    df_mut_h[mask_kosten(df_mut_h)]
                    .groupby("dagboek")["bedrag"].sum()
                    .reset_index().sort_values("bedrag", ascending=False)
                )
                df_kost_dag.columns = ["Dagboek", "Kosten (€)"]
                if not df_kost_dag.empty:
                    st.dataframe(df_kost_dag, use_container_width=True, hide_index=True)
                else:
                    st.info("Geen kostenmutaties in de periode.")

            st.divider()
            st.subheader("📋 Omzet/Kosten per rekening (periode)")
            df_rek = (
                df_mut_h[mask_omzet(df_mut_h) | mask_kosten(df_mut_h)]
                .groupby(["rekeningnummer", "omschrijving", "dc"])["bedrag"]
                .sum().reset_index().sort_values("bedrag", ascending=False)
            )
            df_rek.columns = ["Rekening", "Omschrijving", "D/C", "Bedrag (€)"]
            if not df_rek.empty:
                st.dataframe(df_rek, use_container_width=True, hide_index=True)
            else:
                # Toon alle unieke rekeningen als debug-hulp
                st.info("Geen exploitatierekeningen gevonden. Overzicht van alle rekeningen in de data:")
                df_alle = (
                    df_mut_h.groupby(["rekeningnummer", "omschrijving", "dc"])["bedrag"]
                    .sum().reset_index().sort_values("bedrag", ascending=False)
                )
                df_alle.columns = ["Rekening", "Omschrijving", "D/C", "Bedrag (€)"]
                st.dataframe(df_alle, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("📋 Laatste mutaties")
            st.dataframe(
                df_mut_h.sort_values("boekdatum", ascending=False).head(50)[[
                    "boekdatum", "rekeningnummer", "omschrijving", "dc", "bedrag", "dagboek"
                ]].rename(columns={
                    "boekdatum":      "Boekdatum",
                    "rekeningnummer": "Rekening",
                    "omschrijving":   "Omschrijving",
                    "dc":             "D/C",
                    "bedrag":         "Bedrag (€)",
                    "dagboek":        "Dagboek",
                }),
                use_container_width=True, hide_index=True,
            )

    except Exception as e:
        st.error(f"⚠️ Fout bij laden Cashweb-data: {e}")

    with st.expander("ℹ️ Toelichting"):
        st.markdown("""
        **Databron:** `cashweb.ledger_mutations` gefilterd op `sub_administration = 'alaw'`
        (Amsterdam Warehouse Company).

        **Rekeningindeling (standaard Cashweb):**

        | Reeks | Type |
        |-------|------|
        | 8xxx  | Omzet / Opbrengsten (credit) |
        | 4xxx–7xxx | Kosten / Lasten (debet) |

        **Let op:** als AWC een afwijkend rekeningschema hanteert, pas dan de regex
        `r"^8"` (omzet) en `r"^[4-7]"` (kosten) bovenaan `bereken_fin()` aan.

        **Bruto Marge** = Omzet − directe kosten. Voor een netto-marge zijn ook
        bedrijfskosten (overhead, afschrijvingen) meegenomen via `exploitation_code`
        in `cashweb.ledger_balances`.
        """)


# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#AAAAAA;font-size:0.72rem;"
    "letter-spacing:0.06em;text-transform:uppercase'>"
    "Amsterdam Warehouse Co &nbsp;·&nbsp; Data &amp; Application Platform "
    "&nbsp;·&nbsp; Warehouse KPI Dashboard &nbsp;·&nbsp; 7T Software · HubSpot"
    "</p>",
    unsafe_allow_html=True,
)