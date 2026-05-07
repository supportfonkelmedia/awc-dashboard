import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta, date

# ============================================================
# AMSTERDAM COMPANIES — MT Dashboard  v2
# Covers: AWC · AFC · ACC  (Strategische, Operationele & Tactische KPI's)
# Databronnen: Cashweb · HubSpot (dw_2401) · Sprinter3000
# Placeholders: Hooray · Microsoft Forms · Notion · 7T
#
# Cashweb-logica (bevestigd AFC → verwacht zelfde voor AWC/ACC):
#   - Periodefilter: book_year (string) + book_period (YYMM integer)
#   - Bedragen: Dutch-format string "7.380,49" → REPLACE+CAST conversie
#   - Omzet: dagboek '50' (AWC) of 'VERK' (AFC) → D-kant (debit_credit='D')
#   - Inkoop: dagboek 'INK' → C-kant
#   - FTE-proxy: dagboek 'SAL' → loonkosten als benadering
#   - book_date is ONBETROUWBAAR (sync-vertraging) — gebruik book_period!
# ============================================================

st.set_page_config(
    page_title="MT Dashboard — Amsterdam Companies",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# STYLING
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
      font-family: 'Barlow', sans-serif;
      background-color: #F4F5F7;
      color: #1A1A1A;
  }
  .mt-header {
      background: linear-gradient(135deg, #0D0D0D 0%, #1a1a2e 100%);
      margin: 1.5rem -1rem 0 -1rem;
      padding: 16px 28px;
      display: flex; align-items: center; justify-content: space-between;
      border-bottom: 4px solid #FF6B1A;
  }
  .mt-logo-text {
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 800; font-size: 1.5rem;
      letter-spacing: 0.04em; text-transform: uppercase;
      color: #fff; line-height: 1.1;
  }
  .mt-logo-sub {
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 600; font-size: 0.62rem;
      letter-spacing: 0.22em; text-transform: uppercase;
      color: #FF6B1A; margin-top: 1px;
  }
  .mt-header-right { font-size: 0.78rem; color: #888; letter-spacing: 0.04em; text-align: right;}
  .mt-badge {
      background: #FF6B1A; color: #fff; font-weight: 700;
      padding: 4px 12px; border-radius: 4px; margin-left: 10px;
      font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase;
      font-family: 'Barlow Condensed', sans-serif;
  }
  .mt-subbar {
      background: #fff; margin: 0 -1rem 1.5rem -1rem;
      padding: 10px 28px; border-bottom: 1px solid #E2E5EA;
      display: flex; align-items: center; gap: 8px;
  }
  .mt-subbar-title {
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 800; font-size: 1.4rem;
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
      background-color: #0D0D0D !important; border-right: none !important;
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
      font-weight: 800 !important; font-size: 2.0rem !important;
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
  .kpi-badge.blue   { background: #1a56db; }
  .kpi-badge.red    { background: #c81e1e; }
  .kpi-badge.green  { background: #057a55; }

  .debug-box {
      background: #1e1e2e; border-radius: 6px;
      border-left: 4px solid #FF6B1A;
      padding: 12px 16px; margin: 8px 0;
      font-family: 'Courier New', monospace;
      font-size: 0.78rem; color: #c9d1d9; line-height: 1.6;
  }
  .onduidelijk-box {
      background: #fff3cd; border-radius: 6px;
      border-left: 4px solid #f59e0b;
      padding: 12px 16px; margin: 8px 0;
      font-size: 0.85rem; color: #92400e;
  }
  .info-box {
      background: #e8f4fd; border-radius: 6px;
      border-left: 4px solid #1a56db;
      padding: 12px 16px; margin: 8px 0;
      font-size: 0.83rem; color: #1e3a5f;
  }
  .todo-box {
      background: #f0fdf4; border-radius: 6px;
      border-left: 4px solid #057a55;
      padding: 10px 14px; margin: 6px 0;
      font-size: 0.80rem; color: #14532d;
  }
  .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
now_str = datetime.now().strftime("%A %d %B %Y — %H:%M")
st.markdown(f"""
<div class="mt-header">
  <div>
    <div class="mt-logo-text">Amsterdam Companies</div>
    <div class="mt-logo-sub">AWC &nbsp;·&nbsp; AFC &nbsp;·&nbsp; ACC</div>
  </div>
  <div class="mt-header-right">
    Data &amp; Application Platform &nbsp;·&nbsp; {now_str}
    <span class="mt-badge">MT Dashboard v2</span>
  </div>
</div>
<div class="mt-subbar">
  <div class="mt-subbar-title">Management Team KPI's</div>
  <span class="co-pill active">AWC</span>
  <span class="co-pill active">AFC</span>
  <span class="co-pill active">ACC</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TOP FILTER BAR — compact, boven de tabs
# ══════════════════════════════════════════════════════════════
MAAND_NAMEN = {
    1:"Januari",2:"Februari",3:"Maart",4:"April",5:"Mei",6:"Juni",
    7:"Juli",8:"Augustus",9:"September",10:"Oktober",11:"November",12:"December"
}
huidig_jaar  = datetime.today().year
huidig_maand = datetime.today().month

with st.container():
    _fc1, _fc2, _fc3, _fc4, _fc5 = st.columns([1.2, 2.2, 0.8, 0.8, 2])
    with _fc1:
        boekjaar = st.selectbox(
            "📅 Boekjaar",
            [str(huidig_jaar), str(huidig_jaar-1), str(huidig_jaar-2)],
            index=0, key="top_boekjaar", label_visibility="collapsed",
        )
        st.caption("Boekjaar")
    with _fc2:
        maand_opties = ["Heel jaar"] + [f"{m} — {MAAND_NAMEN[m]}" for m in range(1, 13)]
        gekozen_maand_str = st.selectbox(
            "📆 Periode",
            maand_opties,
            index=min(huidig_maand, 12),
            key="top_periode", label_visibility="collapsed",
        )
        st.caption("Periode")
    with _fc3:
        _start_custom = st.date_input(
            "Van", value=date(int(huidig_jaar), 1, 1),
            key="top_van", label_visibility="collapsed",
        )
        st.caption("Van (Sprinter/HS)")
    with _fc4:
        _eind_custom = st.date_input(
            "Tot", value=date.today(),
            key="top_tot", label_visibility="collapsed",
        )
        st.caption("Tot (Sprinter/HS)")
    with _fc5:
        st.markdown("")  # spacer

st.markdown('<hr style="margin:4px 0 16px 0;border-color:#E2E5EA">', unsafe_allow_html=True)

# ── Periodeberekeningen ───────────────────────────────────────
if gekozen_maand_str == "Heel jaar":
    maanden_filter = list(range(1, 13))
    _periode_label = f"Heel {boekjaar}"
else:
    maand_nr       = int(gekozen_maand_str.split(" — ")[0])
    maanden_filter = [maand_nr]
    _periode_label = f"{MAAND_NAMEN[maand_nr]} {boekjaar}"

# book_period (YYMM): 2604 = april 2026
_yy          = int(str(boekjaar)[-2:])
book_periods = [_yy * 100 + m for m in maanden_filter]
_bp_str      = ", ".join(str(p) for p in book_periods)

# Vorige periode
_yy_v          = _yy - 1
book_periods_v = [_yy_v * 100 + m for m in maanden_filter]
_bp_v_str      = ", ".join(str(p) for p in book_periods_v)
boekjaar_v     = str(int(boekjaar) - 1)

# Laatste maand in de selectie (voor einddatumberekening)
_laatste_m   = maanden_filter[-1]

# Kalenderdata voor HubSpot/Sprinter: gebruik de datumkiezer als override
_start_datum = _start_custom
_eind_datum  = _eind_custom

# ══════════════════════════════════════════════════════════════
# SIDEBAR — alleen databron-status
# ══════════════════════════════════════════════════════════════
st.sidebar.markdown(
    '<div style="font-family:\'Barlow Condensed\',sans-serif;font-weight:800;'
    'font-size:1.0rem;letter-spacing:0.08em;text-transform:uppercase;color:#fff;'
    'border-bottom:1px solid #2a2a2a;padding-bottom:8px;margin-bottom:10px;">'
    '📡 Databronnen</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<div style="font-size:0.68rem;color:#555;letter-spacing:0.04em;line-height:1.9">'
    '🟢 Cashweb &nbsp;&nbsp;&nbsp; <code>dw_2401 / cashweb</code><br>'
    '🟢 HubSpot &nbsp;&nbsp;&nbsp; <code>dw_2401 / hubspot_v2</code><br>'
    '🟢 Sprinter &nbsp;&nbsp;&nbsp; <code>dw_2401 / sprinter3000</code><br>'
    '⏳ Hooray &nbsp;&nbsp;&nbsp;&nbsp; <em>niet verbonden</em><br>'
    '⏳ MS Forms &nbsp;&nbsp; <em>niet verbonden</em><br>'
    '⏳ Notion &nbsp;&nbsp;&nbsp;&nbsp; <em>niet verbonden</em><br>'
    '⏳ 7T Software <em>niet verbonden</em></div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown('<hr style="border-color:#2a2a2a;margin:12px 0">', unsafe_allow_html=True)
st.sidebar.markdown(
    '<div style="font-family:\'Barlow Condensed\',sans-serif;font-weight:800;'
    'font-size:1.0rem;letter-spacing:0.08em;text-transform:uppercase;color:#fff;'
    'border-bottom:1px solid #2a2a2a;padding-bottom:8px;margin-bottom:10px;">'
    '🗓️ Actieve filter</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f'<div style="font-size:0.72rem;color:#aaa;line-height:1.8">'
    f'Boekjaar: <b style="color:#fff">{boekjaar}</b><br>'
    f'Periode: <b style="color:#fff">{_periode_label}</b><br>'
    f'book_period(s): <code>{_bp_str}</code><br>'
    f'Datums: <b style="color:#fff">{_start_datum} → {_eind_datum}</b>'
    f'</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════
# DB CONNECTIE & HELPERS
# ══════════════════════════════════════════════════════════════
_dbconn = pq.dbconnect('dw_2401')

def fetch(query, label="query"):
    """Voer een query uit en geef een DataFrame terug (leeg bij fout)."""
    try:
        df = _dbconn.fetch('dw_2401', query=query, df=True)
        return df if df is not None else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ DB-fout [{label}]: {e}")
        return pd.DataFrame()

def fmt_eur(bedrag):
    """Format een getal als euro string."""
    try:
        b = float(bedrag)
        if abs(b) >= 1_000_000:
            return f"€{b/1_000_000:.2f}M"
        elif abs(b) >= 1_000:
            return f"€{b/1_000:.1f}K"
        else:
            return f"€{b:.0f}"
    except Exception:
        return "—"

def safe_float(x, default=0.0):
    try:
        return float(str(x).replace(",", ".").replace(" ", "")) if x is not None else default
    except Exception:
        return default

def delta_tekst(huidig, vorig):
    try:
        if vorig and float(vorig) != 0:
            pct = ((float(huidig) - float(vorig)) / abs(float(vorig))) * 100
            return f"{pct:+.1f}%"
    except Exception:
        pass
    return None

def onduidelijk_box(tekst):
    st.markdown(f'<div class="onduidelijk-box">⚠️ <b>Meer info nodig:</b><br>{tekst}</div>', unsafe_allow_html=True)

def info_box(tekst):
    st.markdown(f'<div class="info-box">ℹ️ {tekst}</div>', unsafe_allow_html=True)

def todo_box(tekst):
    st.markdown(f'<div class="todo-box">✅ <b>Actiepunt:</b> {tekst}</div>', unsafe_allow_html=True)

def maak_csv(df_ruw, kpi_naam, berekening, filter_info, extra_df=None, extra_label=None):
    """
    Genereer een CSV met twee secties:
      1. Berekenings-metadata (bovenaan als 'header' rijen)
      2. Ruwe data
    Optioneel: een tweede DataFrame als extra verificatietabel.
    Geeft bytes terug (utf-8-sig = Excel-compatibel met Nederlandse tekens).
    """
    buf = io.StringIO()
    # ── Sectie 1: metadata ─────────────────────────────────────
    buf.write("=== BEREKENING ===\n")
    buf.write(f"KPI,{kpi_naam}\n")
    buf.write(f"Gegenereerd,{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    buf.write(f"Periode,{_periode_label}\n")
    buf.write(f"Boekjaar (Cashweb),{boekjaar}\n")
    buf.write(f"book_periods (Cashweb),\"{_bp_str}\"\n")
    buf.write(f"Datumrange (HubSpot/Sprinter),{_start_datum} → {_eind_datum}\n")
    buf.write(f"Filter,\"{filter_info}\"\n")
    buf.write(f"Berekening,\"{berekening}\"\n")
    buf.write("\n")
    # ── Sectie 2: ruwe data ────────────────────────────────────
    buf.write("=== RUWE DATA ===\n")
    if df_ruw is not None and not df_ruw.empty:
        df_ruw.to_csv(buf, index=False)
    else:
        buf.write("(geen data)\n")
    # ── Sectie 3: optionele extra tabel ───────────────────────
    if extra_df is not None and not extra_df.empty:
        buf.write(f"\n=== {extra_label or 'EXTRA DATA'} ===\n")
        extra_df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")

def dl_knop(label, df_ruw, kpi_naam, berekening, filter_info,
            bestandsnaam, extra_df=None, extra_label=None, key=None):
    """Toon een compacte download-knop voor ruwe KPI-data."""
    csv_bytes = maak_csv(df_ruw, kpi_naam, berekening, filter_info, extra_df, extra_label)
    st.download_button(
        label=f"⬇️ {label}",
        data=csv_bytes,
        file_name=bestandsnaam,
        mime="text/csv",
        key=key,
        help=f"Download ruwe data + berekening als CSV\nKPI: {kpi_naam}\nFilter: {filter_info}",
    )

# ── Cashweb SQL helper — bedrag conversie ─────────────────────
# Dutch-format: "7.380,49" → punt = duizendtaldscheider, komma = decimaal
# Stap: TRIM → REPLACE('.','') → REPLACE(',','.') → NULLIF leeg → CAST NUMERIC
CW_AMOUNT = """CAST(
    NULLIF(
        REPLACE(REPLACE(TRIM(COALESCE(amount, '')), '.', ''), ',', '.'),
        ''
    ) AS NUMERIC
)"""

# Debit/credit check — verdedigt tegen 'D', 'DEBET', 'DEBIT' en 'C', 'CREDIT'
CW_IS_D = "UPPER(TRIM(COALESCE(debit_credit, ''))) IN ('D', 'DEBET', 'DEBIT')"
CW_IS_C = "UPPER(TRIM(COALESCE(debit_credit, ''))) IN ('C', 'CREDIT')"

# Omzet (D-kant): dagboek '50' (AWC vermoedelijk) of 'VERK' (AFC bevestigd)
CW_OMZET_DAGBOEKEN = "('50', 'VERK')"

# ── Periode in SQL ────────────────────────────────────────────
def cw_periode_filter(jaar, bp_str):
    """Geef WHERE-clausule terug voor boekjaar + book_periods."""
    return f"book_year = '{jaar}' AND CAST(book_period AS INTEGER) IN ({bp_str})"

# Huidige periode SQL filter
_CW_FILTER   = cw_periode_filter(boekjaar,   _bp_str)
_CW_FILTER_V = cw_periode_filter(boekjaar_v, _bp_v_str)

# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab_samen, tab_fin, tab_com, tab_afc, tab_mensen, tab_tickets = st.tabs([
    "🏠 Samenvatting",
    "💰 Financieel",
    "📈 Commercieel",
    "🚢 AFC (Sprinter)",
    "👥 Mensen & HR",
    "🎫 Tickets & NPS",
])


# ════════════════════════════════════════════════════════════
# GEDEELDE DATA — 1x laden, in meerdere tabs gebruiken
# ════════════════════════════════════════════════════════════

# ── Cashweb omzet (alle admins — huidig + vorig) ─────────────
_SQL_OMZET = """
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
""".format(is_d=CW_IS_D, is_c=CW_IS_C, amt=CW_AMOUNT,
           periode=_CW_FILTER, dagboeken=CW_OMZET_DAGBOEKEN)

_SQL_OMZET_V = """
SELECT
    admin_code,
    SUM(CASE WHEN {is_d} THEN {amt} ELSE 0 END) AS debet_v,
    SUM(CASE WHEN {is_c} THEN {amt} ELSE 0 END) AS credit_v
FROM cashweb.ledger_mutations
WHERE {periode}
  AND journal_code IN {dagboeken}
GROUP BY admin_code
""".format(is_d=CW_IS_D, is_c=CW_IS_C, amt=CW_AMOUNT,
           periode=_CW_FILTER_V, dagboeken=CW_OMZET_DAGBOEKEN)

_df_omzet   = fetch(_SQL_OMZET,   "cw_omzet")
_df_omzet_v = fetch(_SQL_OMZET_V, "cw_omzet_vorig")

# Totale omzet (D-kant dagboek '50'/'VERK')
_totaal_omzet   = _df_omzet["debet"].apply(safe_float).sum()   if not _df_omzet.empty   else 0.0
_totaal_omzet_v = _df_omzet_v["debet_v"].apply(safe_float).sum() if not _df_omzet_v.empty else 0.0

# ── Cashweb inkoop / kosten ───────────────────────────────────
_SQL_INK = """
SELECT
    admin_code,
    SUM(CASE WHEN {is_c} THEN {amt} ELSE 0 END) AS credit_ink,
    COUNT(*) AS mutaties
FROM cashweb.ledger_mutations
WHERE {periode}
  AND journal_code = 'INK'
GROUP BY admin_code
""".format(is_c=CW_IS_C, amt=CW_AMOUNT, periode=_CW_FILTER)

_SQL_INK_V = _SQL_INK.replace(_CW_FILTER, _CW_FILTER_V)

_df_ink   = fetch(_SQL_INK,   "cw_inkoop")
_df_ink_v = fetch(_SQL_INK_V, "cw_inkoop_vorig")

_totaal_inkoop   = abs(_df_ink["credit_ink"].apply(safe_float).sum())   if not _df_ink.empty   else 0.0
_totaal_inkoop_v = abs(_df_ink_v["credit_ink"].apply(safe_float).sum()) if not _df_ink_v.empty else 0.0

# ── Cashweb lonen (SAL dagboek — FTE proxy) ───────────────────
# Loonkosten zitten in dagboek 'SAL', credit-kant = werkgeverslast
_SQL_SAL = """
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
""".format(is_d=CW_IS_D, is_c=CW_IS_C, amt=CW_AMOUNT, periode=_CW_FILTER)

_df_sal = fetch(_SQL_SAL, "cw_salarissen")

# ── Cashweb bruto marge ───────────────────────────────────────
_brutomarge   = _totaal_omzet   - _totaal_inkoop
_brutomarge_v = _totaal_omzet_v - _totaal_inkoop_v
_marge_pct    = (_brutomarge / _totaal_omzet * 100) if _totaal_omzet > 0 else 0.0
_marge_pct_v  = (_brutomarge_v / _totaal_omzet_v * 100) if _totaal_omzet_v > 0 else 0.0

# ── Sprinter: zendingen ───────────────────────────────────────
_df_ship = fetch(f"""
    SELECT
        s.shipment_id, s.shipment_number, s.report_date,
        s.shipment_mode, s.shipment_status_code, s.department,
        s.total_sales_amount, s.total_purchase_amount, s.total_gpm_amount,
        s.total_pieces, s.customer_company_id,
        c.name AS klant_naam
    FROM sprinter3000.shipments s
    LEFT JOIN sprinter3000.companies c ON s.customer_company_id = c.company_id
    WHERE s.report_date >= '{_start_datum}' AND s.report_date <= '{_eind_datum}'
    ORDER BY s.report_date DESC
""", "sprinter_ship")

_df_ship_v = fetch(f"""
    SELECT COUNT(*) AS n, SUM(total_gpm_amount) AS marge
    FROM sprinter3000.shipments
    WHERE report_date >= '{date(int(boekjaar)-1, maanden_filter[0], 1)}'
      AND report_date <= '{date(int(boekjaar)-1, _laatste_m,
                               (date(int(boekjaar)-1, _laatste_m % 12+1, 1) - timedelta(days=1)).day
                               if _laatste_m < 12 else 31)}'
""", "sprinter_ship_v")

if not _df_ship.empty:
    _df_ship["total_gpm_amount"]   = pd.to_numeric(_df_ship["total_gpm_amount"],   errors="coerce").fillna(0)
    _df_ship["total_sales_amount"] = pd.to_numeric(_df_ship["total_sales_amount"], errors="coerce").fillna(0)
    _df_ship["report_date"]        = pd.to_datetime(_df_ship["report_date"],        errors="coerce")

_n_ship     = len(_df_ship)   if not _df_ship.empty   else 0
_marge_ship = _df_ship["total_gpm_amount"].sum() if not _df_ship.empty else 0
_n_ship_v   = safe_float(_df_ship_v["n"].iloc[0])    if not _df_ship_v.empty else 0
_marge_v    = safe_float(_df_ship_v["marge"].iloc[0]) if not _df_ship_v.empty else 0

# ── FTE proxy (SAL dagboek) ────────────────────────────────────
_loon_totaal = 0.0
_fte_proxy   = 0.0
if not _df_sal.empty:
    _df_sal["loon_debet"]  = _df_sal["loon_debet"].apply(safe_float)
    _df_sal["loon_credit"] = _df_sal["loon_credit"].apply(safe_float)
    # Loonkosten = debet-kant van SAL (netto loonbetaling aan werknemers)
    _loon_totaal = _df_sal["loon_debet"].sum()

# ── Admin count (voor Triple LOB berekening overal) ─────────────
_df_admins_vroeg = fetch("""
    SELECT DISTINCT admin_code FROM cashweb.ledger_mutations
    WHERE admin_code IS NOT NULL AND admin_code != ''
""", "admin_count")
_n_admins = len(_df_admins_vroeg) if not _df_admins_vroeg.empty else 0

# ════════════════════════════════════════════════════════════
# TAB 1 — SAMENVATTING
# ════════════════════════════════════════════════════════════
with tab_samen:
    st.markdown('<div class="kpi-badge orange">MT Samenvatting</div>', unsafe_allow_html=True)
    st.subheader(f"Strategische KPI's — {_periode_label}")
    st.caption("High-level overzicht voor MT. Klik door naar tabs voor details, berekeningen en debug-info.")

    # ── Strategische metrics rij 1 ────────────────────────────
    st.markdown("### 💰 Financieel (Cashweb)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Omzet", fmt_eur(_totaal_omzet),
                delta=delta_tekst(_totaal_omzet, _totaal_omzet_v),
                help=f"📌 DEFINITIE\n"
                     f"Totale gefactureerde omzet aan klanten (AWC + AFC + ACC).\n"
                     f"Elke verkoopfactuur bestaat uit 2 boekingsregels:\n"
                     f"  • D-kant (debit_credit='D') = klant schuldt dit bedrag\n"
                     f"  • Lege kant = omzetrekening (tegenboeking, telt niet mee)\n"
                     f"Alleen de D-kant tellen = het factuurbedrag.\n"
                     f"\n"
                     f"📐 FORMULE\n"
                     f"SUM(amount) WHERE debit_credit IN ('D','DEBET','DEBIT')\n"
                     f"AND journal_code IN ('50','VERK')\n"
                     f"\n"
                     f"🔢 RUWE BEREKENING\n"
                     f"Huidig  ({_periode_label}):  {fmt_eur(_totaal_omzet)}\n"
                     f"Vorig   ({boekjaar_v}):  {fmt_eur(_totaal_omzet_v)}\n"
                     f"Mutaties in dagboek 50/VERK: zie download\n"
                     f"\n"
                     f"🗓️ FILTER\n"
                     f"book_year = '{boekjaar}'\n"
                     f"book_period IN ({_bp_str})\n"
                     f"book_period formaat: YYMM → {_bp_str.split(',')[0].strip()} = {MAAND_NAMEN[maanden_filter[0]]} {boekjaar}\n"
                     f"\n"
                     f"⚙️ BEDRAGCONVERSIE\n"
                     f"amount is Dutch-format string: '7.380,49'\n"
                     f"REPLACE('.','') → REPLACE(',','.') → CAST NUMERIC")
    col2.metric("Inkoopkosten", fmt_eur(_totaal_inkoop),
                delta=delta_tekst(_totaal_inkoop, _totaal_inkoop_v),
                help=f"📌 DEFINITIE\n"
                     f"Totale inkoopkosten = leveranciersfacturen (directe kosten).\n"
                     f"Elke inkoopfactuur bestaat uit 2 boekingsregels:\n"
                     f"  • C-kant (debit_credit='C') = bedrijf schuldt leverancier\n"
                     f"  • Lege kant = kostenrekening (tegenboeking)\n"
                     f"C-bedragen zijn negatief opgeslagen → ABS() voor positief getal.\n"
                     f"\n"
                     f"📐 FORMULE\n"
                     f"ABS(SUM(amount)) WHERE debit_credit IN ('C','CREDIT')\n"
                     f"AND journal_code = 'INK'\n"
                     f"\n"
                     f"🔢 RUWE BEREKENING\n"
                     f"Huidig  ({_periode_label}):  {fmt_eur(_totaal_inkoop)}\n"
                     f"Vorig   ({boekjaar_v}):  {fmt_eur(_totaal_inkoop_v)}\n"
                     f"\n"
                     f"🗓️ FILTER\n"
                     f"book_year = '{boekjaar}'\n"
                     f"book_period IN ({_bp_str})\n"
                     f"\n"
                     f"⚠️ AANNAME\n"
                     f"Dagboek 'INK' = alle directe inkoopkosten.\n"
                     f"Overige operationele kosten (huur, personeel etc.) staan in andere dagboeken.")
    col3.metric("Brutomarge", fmt_eur(_brutomarge),
                delta=delta_tekst(_brutomarge, _brutomarge_v),
                help=f"📌 DEFINITIE\n"
                     f"Brutomarge = wat er overblijft van de omzet na aftrek van directe inkoopkosten.\n"
                     f"Geeft aan hoe winstgevend de kernactiviteit is vóór bedrijfskosten.\n"
                     f"\n"
                     f"📐 FORMULE\n"
                     f"Brutomarge = Omzet − Inkoopkosten\n"
                     f"           = D-kant dagboek 50/VERK − ABS(C-kant dagboek INK)\n"
                     f"\n"
                     f"🔢 RUWE BEREKENING\n"
                     f"Omzet:        {fmt_eur(_totaal_omzet)}\n"
                     f"− Inkoop:     {fmt_eur(_totaal_inkoop)}\n"
                     f"= Brutomarge: {fmt_eur(_brutomarge)}\n"
                     f"\n"
                     f"Vorige periode ({boekjaar_v}): {fmt_eur(_brutomarge_v)}\n"
                     f"\n"
                     f"🗓️ FILTER\n"
                     f"book_year = '{boekjaar}' | book_period IN ({_bp_str})")
    col4.metric("Marge %", f"{_marge_pct:.1f}%",
                delta=delta_tekst(_marge_pct, _marge_pct_v),
                help=f"📌 DEFINITIE\n"
                     f"Bruto marge % = het percentage van de omzet dat overblijft na directe inkoopkosten.\n"
                     f"Benchmark: hogere marge % = hogere toegevoegde waarde per euro omzet.\n"
                     f"\n"
                     f"📐 FORMULE\n"
                     f"Marge % = Brutomarge / Omzet × 100\n"
                     f"\n"
                     f"🔢 RUWE BEREKENING\n"
                     f"{fmt_eur(_brutomarge)} / {fmt_eur(_totaal_omzet)} × 100 = {_marge_pct:.1f}%\n"
                     f"Vorige periode: {fmt_eur(_brutomarge_v)} / {fmt_eur(_totaal_omzet_v)} × 100 = {_marge_pct_v:.1f}%\n"
                     f"\n"
                     f"🗓️ FILTER\n"
                     f"book_year = '{boekjaar}' | book_period IN ({_bp_str})")

    # ── Omzet per admin ───────────────────────────────────────
    if not _df_omzet.empty:
        _df_omzet["debet"] = _df_omzet["debet"].apply(safe_float)
        _per_admin = _df_omzet.groupby("admin_code")["debet"].sum().reset_index()
        _per_admin.columns = ["Admin", "Omzet"]
        if len(_per_admin) > 1:
            _admin_cols = st.columns(len(_per_admin))
            for i, row in _per_admin.iterrows():
                _admin_cols[i].metric(f"Omzet — {row['Admin']}", fmt_eur(row['Omzet']))

    st.markdown("---")
    st.markdown("### 🚢 AFC — Sprinter")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Zendingen AFC", str(_n_ship), delta=delta_tekst(_n_ship, _n_ship_v),
                 help=f"📌 DEFINITIE\n"
                      f"Totaal aantal uitgevoerde transportzendingen door AFC in de periode.\n"
                      f"Elke zending = één shipment_id in Sprinter3000.\n"
                      f"\n"
                      f"📐 FORMULE\n"
                      f"COUNT(shipment_id) FROM sprinter3000.shipments\n"
                      f"\n"
                      f"🔢 RUWE BEREKENING\n"
                      f"Huidig  ({_start_datum} → {_eind_datum}): {_n_ship} zendingen\n"
                      f"Vorig   (zelfde periode {int(boekjaar)-1}):    {_n_ship_v:.0f} zendingen\n"
                      f"\n"
                      f"🗓️ FILTER\n"
                      f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'\n"
                      f"⚠️ report_date = rapportagedatum in Sprinter (niet per se verzenddatum)")
    col_b.metric("Marge AFC (GPM)", fmt_eur(_marge_ship), delta=delta_tekst(_marge_ship, _marge_v),
                 help=f"📌 DEFINITIE\n"
                      f"Totale bruto winstmarge AFC = verkoopprijs minus inkoopprijs per zending.\n"
                      f"GPM = Gross Profit Margin. Berekend door Sprinter zelf.\n"
                      f"\n"
                      f"📐 FORMULE\n"
                      f"SUM(total_gpm_amount)\n"
                      f"waarbij total_gpm_amount = total_sales_amount − total_purchase_amount\n"
                      f"\n"
                      f"🔢 RUWE BEREKENING\n"
                      f"Totale GPM huidig:  {fmt_eur(_marge_ship)}\n"
                      f"Totale GPM vorig:   {fmt_eur(_marge_v)}\n"
                      f"Aantal zendingen:   {_n_ship}\n"
                      f"Gem. GPM/zending:   {fmt_eur(_marge_ship/_n_ship) if _n_ship>0 else '—'}\n"
                      f"\n"
                      f"🗓️ FILTER\n"
                      f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'\n"
                      f"⚠️ Zijn alle kosten meegenomen in total_purchase_amount?\n"
                      f"   Controleer of douanekosten/extra handling ook inbegrepen zijn.")
    col_c.metric("Gem. Marge / Zending",
                 fmt_eur(_marge_ship / _n_ship) if _n_ship > 0 else "—",
                 help=f"📌 DEFINITIE\n"
                      f"Gemiddelde winstmarge per individuele zending (AFC).\n"
                      f"Geeft inzicht in de winstgevendheid per transportopdracht.\n"
                      f"\n"
                      f"📐 FORMULE\n"
                      f"Gem. Marge/Zending = SUM(total_gpm_amount) / COUNT(shipment_id)\n"
                      f"\n"
                      f"🔢 RUWE BEREKENING\n"
                      f"{fmt_eur(_marge_ship)} / {_n_ship} zendingen = {fmt_eur(_marge_ship/_n_ship) if _n_ship>0 else '—'}\n"
                      f"\n"
                      f"🗓️ FILTER\n"
                      f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'")

    # ── Download samenvatting ────────────────────────────────
    st.markdown("---")
    _dl_c1, _dl_c2, _dl_c3 = st.columns(3)
    with _dl_c1:
        dl_knop("Omzet & Marge (Cashweb)", _df_omzet, "Omzet & Brutomarge",
                "SUM(amount D-kant) dagboek 50/VERK",
                f"book_year='{boekjaar}' AND book_period IN ({_bp_str})",
                f"samenvatting_omzet_{boekjaar}.csv", key="dl_sam_omzet")
    with _dl_c2:
        dl_knop("Zendingen AFC (Sprinter)", _df_ship, "Zendingen & GPM",
                "SUM(total_gpm_amount)",
                f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'",
                f"samenvatting_sprinter_{_start_datum}.csv", key="dl_sam_ship")
    with _dl_c3:
        if not _df_ink.empty:
            dl_knop("Inkoop (Cashweb)", _df_ink, "Inkoopkosten",
                    "ABS(SUM(amount C-kant)) dagboek INK",
                    f"book_year='{boekjaar}' AND book_period IN ({_bp_str})",
                    f"samenvatting_inkoop_{boekjaar}.csv", key="dl_sam_ink")

    st.markdown("---")
    st.markdown("### ⏳ KPI's — actie vereist vóór automatisering")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.info("**EBITDA**\n\nAccountmapping bevestigen\nmet boekhouding (Frits)")
    with c2:
        st.info("**Bruto Margin / FTE**\n\nLoonkosten via SAL ✅\nFTE-teller: Hooray ⏳")
    with c3:
        st.warning("**NPS / eNPS**\n\nNog toe te voegen in\nHubSpot Service Hub")
    with c4:
        st.warning("**A/B Players &\nIntern/Extern**\n\nHandmatig of via\nVIE People / Hooray")

    # ── Debug: wat zit er in de data ──────────────────────────
    with st.expander("🔍 Debug — Cashweb omzet-query (hoe berekend)"):
        st.markdown("**SQL die gebruikt wordt voor omzet:**")
        st.code(_SQL_OMZET, language="sql")
        st.markdown("**Ruwe uitkomst per admin + dagboek:**")
        if not _df_omzet.empty:
            _show = _df_omzet.copy()
            _show["debet"]  = _show["debet"].apply(safe_float).apply(fmt_eur)
            _show["credit"] = _show["credit"].apply(safe_float).apply(fmt_eur)
            st.dataframe(_show, use_container_width=True, hide_index=True)
        else:
            st.warning("Geen Cashweb omzetdata — zijn dagboeken '50' en 'VERK' aanwezig?")

        _yy_label = boekjaar[-2:]
        st.markdown(f"""
<div class="debug-box">
Omzet-logica (bevestigd voor AFC/pgl1 — verwacht zelfde voor AWC/ACC):<br>
  Dagboek '50' of 'VERK' → factuur bestaat uit 2 regels per boeking:<br>
    regel 1: debit_credit='D' → debiteuren (klant schuldt bedrag)<br>
    regel 2: debit_credit=''  → omzetrekening + BTW (tegenboeking)<br>
  Omzet = SUM van D-kant ONLY → anders heffen D en lege regels elkaar op → netto ≈ 0<br><br>
  Bedragen zijn Dutch-format strings: "7.380,49"<br>
  Conversie: REPLACE('.','') → REPLACE(',','.') → CAST NUMERIC<br><br>
⚠️ book_date is ONBETROUWBAAR (sync-vertraging). Filter altijd op book_year + book_period!<br>
⚠️ Periodeformat: YYMM integer → {_yy_label}04 = april {boekjaar}
</div>""", unsafe_allow_html=True)

    with st.expander("🔍 Debug — Cashweb dagboeken-check (welke dagboeken bestaan er?)"):
        _df_jc = fetch(f"""
            SELECT journal_code, admin_code,
                   COUNT(*) AS mutaties,
                   SUM({CW_AMOUNT}) AS totaal_bedrag
            FROM cashweb.ledger_mutations
            WHERE {_CW_FILTER}
            GROUP BY journal_code, admin_code
            ORDER BY mutaties DESC
        """, "dagboeken_check")
        if not _df_jc.empty:
            _df_jc["totaal_bedrag"] = _df_jc["totaal_bedrag"].apply(safe_float).apply(fmt_eur)
            st.dataframe(_df_jc, use_container_width=True, hide_index=True)
            st.markdown("""
<div class="debug-box">
Verwachte dagboeken in AWC (uit screenshot 2025):<br>
  50     → Verkoop (groots: debet ≈ €24.7M = debiteurenrekening)<br>
  INK    → Inkoop<br>
  RAB311 → Bank Rabobank 311<br>
  RAB933 → Bank Rabobank 933<br>
  MEMO   → Memoriaal (correcties)<br>
  SAL    → Salarissen<br>
  OBBOEK → Openingsboek<br><br>
AFC gebruikt 'VERK' i.p.v. '50' voor verkoop — beide worden nu meegenomen.<br>
Als de kolom 'totaal_bedrag' voor '50' groot is, klopt de logica.
</div>""", unsafe_allow_html=True)
        else:
            st.warning("Geen dagboek-data — check Cashweb verbinding.")


# ════════════════════════════════════════════════════════════
# TAB 2 — FINANCIEEL
# ════════════════════════════════════════════════════════════
with tab_fin:
    st.markdown('<div class="kpi-badge orange">Financieel — Cashweb</div>', unsafe_allow_html=True)
    st.subheader(f"Financiële KPI's — {_periode_label}")

    # ═══ Omzet per admin + trend ══════════════════════════════
    st.markdown("## 📊 Omzet per entiteit")

    if not _df_omzet.empty:
        _df_omzet["debet"]  = _df_omzet["debet"].apply(safe_float)
        _df_omzet["credit"] = _df_omzet["credit"].apply(safe_float)

        _per_adm = _df_omzet.groupby("admin_code")["debet"].sum().reset_index()
        _per_adm.columns = ["Admin", "Omzet (€)"]
        _adm_cols = st.columns(max(len(_per_adm), 1))
        for i, row in _per_adm.iterrows():
            _adm_cols[min(i, len(_adm_cols)-1)].metric(
                f"Omzet — {row['Admin']}", fmt_eur(row["Omzet (€)"])
            )

        # Maandtrend omzet
        _df_trend = fetch(f"""
            SELECT
                admin_code,
                CAST(book_period AS INTEGER) AS periode,
                SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet
            FROM cashweb.ledger_mutations
            WHERE book_year = '{boekjaar}'
              AND journal_code IN {CW_OMZET_DAGBOEKEN}
            GROUP BY admin_code, CAST(book_period AS INTEGER)
            ORDER BY periode
        """, "fin_trend")

        if not _df_trend.empty:
            _df_trend["omzet"]   = _df_trend["omzet"].apply(safe_float)
            _df_trend["maand"]   = (_df_trend["periode"] % 100).astype(int).map(MAAND_NAMEN).fillna(_df_trend["periode"].astype(str))
            _df_trend["periode"] = pd.to_numeric(_df_trend["periode"], errors="coerce")
            _df_trend = _df_trend.sort_values("periode")

            st.markdown("**Omzet per maand (alle admins):**")
            _pivot = _df_trend.pivot_table(
                index="maand", columns="admin_code", values="omzet", aggfunc="sum"
            ).fillna(0)
            # Herstel volgorde (jan → dec)
            _mnd_order = [MAAND_NAMEN[m] for m in range(1,13) if MAAND_NAMEN[m] in _pivot.index]
            _pivot = _pivot.reindex(_mnd_order)
            st.bar_chart(_pivot)

        with st.expander("🔍 Debug — Omzet detail + SQL"):
            st.code(_SQL_OMZET, language="sql")
            st.markdown("**Ruwe data (huidig):**")
            st.dataframe(_df_omzet, use_container_width=True, hide_index=True)
            if not _df_omzet_v.empty:
                st.markdown("**Vorige periode:**")
                _df_omzet_v["debet_v"]  = _df_omzet_v["debet_v"].apply(safe_float).apply(fmt_eur)
                _df_omzet_v["credit_v"] = _df_omzet_v["credit_v"].apply(safe_float).apply(fmt_eur)
                st.dataframe(_df_omzet_v, use_container_width=True, hide_index=True)
        dl_knop("Download omzet + vorige periode", _df_omzet, "Omzet per admin/dagboek",
                "SUM(amount) WHERE debit_credit='D' AND journal_code IN ('50','VERK')",
                f"book_year='{boekjaar}' AND book_period IN ({_bp_str})",
                f"omzet_{boekjaar}.csv",
                extra_df=_df_omzet_v if not _df_omzet_v.empty else None,
                extra_label="VORIGE PERIODE", key="dl_fin_omzet")
        st.markdown(f"""
<div class="debug-box">
Omzet = D-kant dagboek '50' of 'VERK'<br>
Huidige periodes (book_period): {_bp_str}<br>
Vorige periodes (book_period):  {_bp_v_str}<br><br>
Totaal huidig:  {fmt_eur(_totaal_omzet)}<br>
Totaal vorig:   {fmt_eur(_totaal_omzet_v)}<br>
Delta:          {delta_tekst(_totaal_omzet, _totaal_omzet_v) or 'n.v.t.'}
</div>""", unsafe_allow_html=True)
    else:
        onduidelijk_box("""
        Geen Cashweb omzetdata gevonden voor de geselecteerde periode.<br>
        Mogelijke oorzaken:<br>
        • Dagboek heet anders dan '50' of 'VERK' voor deze administratie<br>
        • book_period waarden kloppen niet — zie debug hieronder<br>
        • Cashweb connector niet actief
        """)

    st.markdown("---")

    # ═══ Inkoop & Brutomarge ══════════════════════════════════
    st.markdown("## 💹 Brutomarge (Omzet − Inkoop)")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Omzet (VERK/50)", fmt_eur(_totaal_omzet), delta=delta_tekst(_totaal_omzet, _totaal_omzet_v),
                  help=f"📌 DEFINITIE\n"
                       f"Omzet = gefactureerde bedragen aan klanten via het verkoopdagboek.\n"
                       f"Dagboek '50' (AWC) of 'VERK' (AFC): elke factuur = 2 regels.\n"
                       f"  D-kant = debiteur (klant schuldt) → dit is de omzet.\n"
                       f"  Lege kant = omzet/BTW rekening → NIET meetellen.\n"
                       f"\n"
                       f"📐 FORMULE\n"
                       f"SUM(amount) WHERE debit_credit IN ('D','DEBET','DEBIT')\n"
                       f"AND journal_code IN ('50','VERK')\n"
                       f"\n"
                       f"🔢 RUWE BEREKENING\n"
                       f"Huidig  ({_periode_label}):   {fmt_eur(_totaal_omzet)}\n"
                       f"Vorig   ({boekjaar_v}):   {fmt_eur(_totaal_omzet_v)}\n"
                       f"Δ:                          {delta_tekst(_totaal_omzet, _totaal_omzet_v) or 'n.v.t.'}\n"
                       f"\n"
                       f"🗓️ FILTER\n"
                       f"book_year = '{boekjaar}'\n"
                       f"book_period IN ({_bp_str})\n"
                       f"⚠️ book_date NIET gebruikt (sync-vertraging in Cashweb)\n"
                       f"\n"
                       f"⚙️ BEDRAGCONVERSIE\n"
                       f"'7.380,49' → REPLACE('.','') → '7380,49'\n"
                       f"→ REPLACE(',','.') → '7380.49' → CAST NUMERIC")
    col_m2.metric("Inkoop (INK)", fmt_eur(_totaal_inkoop), delta=delta_tekst(_totaal_inkoop, _totaal_inkoop_v),
                  help=f"📌 DEFINITIE\n"
                       f"Inkoopkosten = leveranciersfacturen geboekt in dagboek INK.\n"
                       f"Elke inkoopfactuur = 2 regels:\n"
                       f"  C-kant = crediteur (bedrijf schuldt leverancier) → negatief bedrag.\n"
                       f"  Lege kant = kostenrekening → NIET meetellen.\n"
                       f"ABS() omdat C-bedragen negatief opgeslagen zijn.\n"
                       f"\n"
                       f"📐 FORMULE\n"
                       f"ABS(SUM(amount)) WHERE debit_credit IN ('C','CREDIT')\n"
                       f"AND journal_code = 'INK'\n"
                       f"\n"
                       f"🔢 RUWE BEREKENING\n"
                       f"Huidig  ({_periode_label}):   {fmt_eur(_totaal_inkoop)}\n"
                       f"Vorig   ({boekjaar_v}):   {fmt_eur(_totaal_inkoop_v)}\n"
                       f"Δ:                          {delta_tekst(_totaal_inkoop, _totaal_inkoop_v) or 'n.v.t.'}\n"
                       f"\n"
                       f"🗓️ FILTER\n"
                       f"book_year = '{boekjaar}' | book_period IN ({_bp_str})")
    col_m3.metric("Brutomarge", fmt_eur(_brutomarge), delta=delta_tekst(_brutomarge, _brutomarge_v),
                  help=f"📌 DEFINITIE\n"
                       f"Brutomarge = omzet min directe inkoopkosten.\n"
                       f"Toon winstgevendheid van de kernactiviteit vóór personeels- en andere bedrijfskosten.\n"
                       f"\n"
                       f"📐 FORMULE\n"
                       f"Brutomarge = Omzet (50/VERK D-kant) − Inkoop (INK C-kant)\n"
                       f"\n"
                       f"🔢 RUWE BEREKENING\n"
                       f"  Omzet:          {fmt_eur(_totaal_omzet)}\n"
                       f"− Inkoopkosten:   {fmt_eur(_totaal_inkoop)}\n"
                       f"= Brutomarge:     {fmt_eur(_brutomarge)}\n"
                       f"\n"
                       f"Vorige periode ({boekjaar_v}):\n"
                       f"  {fmt_eur(_totaal_omzet_v)} − {fmt_eur(_totaal_inkoop_v)} = {fmt_eur(_brutomarge_v)}\n"
                       f"\n"
                       f"🗓️ FILTER\n"
                       f"book_year = '{boekjaar}' | book_period IN ({_bp_str})")
    col_m4.metric("Marge %", f"{_marge_pct:.1f}%", delta=delta_tekst(_marge_pct, _marge_pct_v),
                  help=f"📌 DEFINITIE\n"
                       f"Bruto marge % = percentage van omzet dat overblijft na directe kosten.\n"
                       f"\n"
                       f"📐 FORMULE\n"
                       f"Marge % = Brutomarge / Omzet × 100\n"
                       f"\n"
                       f"🔢 RUWE BEREKENING\n"
                       f"Huidig: {fmt_eur(_brutomarge)} / {fmt_eur(_totaal_omzet)} × 100 = {_marge_pct:.1f}%\n"
                       f"Vorig:  {fmt_eur(_brutomarge_v)} / {fmt_eur(_totaal_omzet_v)} × 100 = {_marge_pct_v:.1f}%\n"
                       f"\n"
                       f"🗓️ FILTER\n"
                       f"book_year = '{boekjaar}' | book_period IN ({_bp_str})")

    dl_knop("Download inkoop ruwe data", _df_ink, "Inkoopkosten (INK)",
            "ABS(SUM(amount)) WHERE debit_credit='C' AND journal_code='INK'",
            f"book_year='{boekjaar}' AND book_period IN ({_bp_str})",
            f"inkoop_{boekjaar}.csv",
            extra_df=_df_ink_v if not _df_ink_v.empty else None,
            extra_label="VORIGE PERIODE", key="dl_fin_ink")
    with st.expander("🔍 Debug — Inkoop SQL + data"):
        st.code(_SQL_INK, language="sql")
        if not _df_ink.empty:
            _df_ink["credit_ink"] = _df_ink["credit_ink"].apply(safe_float)
            st.dataframe(_df_ink, use_container_width=True, hide_index=True)
        else:
            st.warning("Geen INK dagboek-data gevonden.")
        st.markdown(f"""
<div class="debug-box">
Inkoop-logica (bevestigd AFC — verwacht zelfde patroon AWC/ACC):<br>
  Dagboek 'INK' → leveranciersfactuur = 2 regels:<br>
    regel 1: debit_credit='C' → crediteur (bedrijf schuldt leverancier)<br>
    regel 2: debit_credit=''  → kostenrekening (tegenboeking)<br>
  Inkoopkosten = ABS(SUM van C-kant) want C-bedragen zijn negatief opgeslagen<br><br>
Totaal inkoop huidig:   {fmt_eur(_totaal_inkoop)}<br>
Totaal inkoop vorig:    {fmt_eur(_totaal_inkoop_v)}<br>
Brutomarge:             {fmt_eur(_brutomarge)}<br>
Marge %:                {_marge_pct:.1f}%
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ═══ EBITDA ═══════════════════════════════════════════════
    st.markdown("## 💰 EBITDA (benadering)")

    onduidelijk_box("""
    EBITDA = Brutomarge − Overige operationele kosten + Afschrijvingen terugvoegen.<br>
    <b>Wat nog bevestigd moet worden:</b><br>
    • Welk dagboek of rekeningreeks = overige operationele kosten (niet-inkoop)?<br>
      Uit de screenshot: MEMO (correcties), SAL (lonen), RAB (bank) — maar welke rekeningen = opex?<br>
    • Welke rekeningreeks = afschrijvingen (om bij EBITDA op te tellen)?<br>
    <b>Huidige benadering:</b> Brutomarge (Omzet − INK) als EBITDA-proxy.<br>
    <b>Actiepunt:</b> bevestig rekeningschema met Frits/boekhouding. Zie debug hieronder.
    """)

    # Toon het rekeningschema via ledger_balances zodat Frits kan aanwijzen
    _df_bal = fetch(f"""
        SELECT
            admin_code,
            account_number,
            description,
            exploitation_code,
            CAST(NULLIF(REPLACE(REPLACE(TRIM(COALESCE(period_amounts_debit,'')),  '.',''),',','.'), '') AS NUMERIC) AS p_debit,
            CAST(NULLIF(REPLACE(REPLACE(TRIM(COALESCE(period_amounts_credit,'')), '.',''),',','.'), '') AS NUMERIC) AS p_credit,
            CAST(NULLIF(REPLACE(REPLACE(TRIM(COALESCE(period_amounts_result,'')), '.',''),',','.'), '') AS NUMERIC) AS p_result
        FROM cashweb.ledger_balances
        WHERE book_year = '{boekjaar}'
          AND account_number IS NOT NULL
        ORDER BY admin_code, account_number
    """, "fin_balances")

    if not _df_bal.empty:
        _df_bal["account_prefix"] = _df_bal["account_number"].str[:1]
        _prefix_sum = _df_bal.groupby(["admin_code","account_prefix"]).agg(
            resultaat=("p_result","sum"), rekeningen=("account_number","count")
        ).reset_index()

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("**Resultaat per rekeningnummer-prefix (per admin):**")
            st.dataframe(_prefix_sum, use_container_width=True, hide_index=True)
        with col_b2:
            st.markdown("**Exploitation_code verdeling:**")
            _expl = _df_bal.groupby(["admin_code","exploitation_code"]).agg(
                resultaat=("p_result","sum"), rekeningen=("account_number","count")
            ).reset_index()
            st.dataframe(_expl, use_container_width=True, hide_index=True)

        with st.expander("🔍 Debug — Volledig rekeningschema (gebruik dit voor EBITDA-mapping)"):
            _col_filter = st.text_input("Filter op account_number prefix (bijv. '4', '8')", value="", key="acc_filter")
            _df_bal_show = _df_bal[_df_bal["account_prefix"] == _col_filter] if _col_filter else _df_bal
            st.dataframe(
                _df_bal_show[["admin_code","account_number","description","exploitation_code","p_debit","p_credit","p_result"]].head(100),
                use_container_width=True, hide_index=True
            )
            st.markdown("""
<div class="debug-box">
Gebruik exploitation_code om W&V-rekeningen te scheiden van balansrekeningen:<br>
  Leeg = balansrekening (activa/passiva)<br>
  Gevuld = exploitatierekening (omzet/kosten → relevant voor EBITDA)<br><br>
EBITDA-definitie die gebouwd moet worden:<br>
  Omzet       = account-reeks X (bijv. 8xxx)<br>
  - Directe kosten = account-reeks Y (bijv. 6xxx of 7xxx) [inkoop, lonen, overig]<br>
  = Bedrijfsresultaat (EBIT minus afschrijvingen)<br>
  + Afschrijvingen/amortisatie = account-reeks Z<br>
  = EBITDA<br><br>
Wijs de prefixen aan via het rekeningschema hierboven, dan verwerk ik de formule.
</div>""", unsafe_allow_html=True)
    else:
        st.warning("Geen ledger_balances data beschikbaar.")

    st.markdown("---")

    # ═══ Revenue per LOB / sub_administration ════════════════
    st.markdown("## 🏢 Revenue per entiteit / LOB")

    onduidelijk_box("""
    <b>LOB-definitie in Cashweb:</b> meest waarschijnlijk = <code>sub_administration</code> = entiteit (AWC/AFC/ACC).<br>
    Of zijn er aparte LOB-tags per entiteit (opslag / transport / customs)?<br>
    Huidige weergave: omzet per <code>admin_code</code> + <code>sub_administration</code>.<br>
    <b>Actiepunt:</b> bevestig met Floor of er een ander LOB-veld bestaat in Cashweb.
    """)

    if not _df_omzet.empty:
        _df_lob = _df_omzet.groupby(["admin_code","sub_administration"])["debet"].sum().reset_index()
        _df_lob["debet_fmt"] = _df_lob["debet"].apply(safe_float).apply(fmt_eur)
        st.dataframe(_df_lob.rename(columns={
            "admin_code":"Admin", "sub_administration":"Sub-admin (LOB proxy)",
            "debet":"Omzet (€)", "debet_fmt":"Omzet"
        }), use_container_width=True, hide_index=True)

        with st.expander("🔍 Debug — Wat zit er in sub_administration?"):
            _df_sub_dist = fetch(f"""
                SELECT sub_administration, admin_code, COUNT(*) AS mutaties
                FROM cashweb.ledger_mutations
                WHERE {_CW_FILTER}
                GROUP BY sub_administration, admin_code
                ORDER BY mutaties DESC
            """, "sub_admin_dist")
            if not _df_sub_dist.empty:
                st.dataframe(_df_sub_dist, use_container_width=True, hide_index=True)
                st.markdown("""
<div class="debug-box">
sub_administration moet in theorie AWC / AFC / ACC onderscheiden.<br>
Als je hier 1 waarde ziet voor 3 admins, zijn de entiteiten niet correct gesplitst in Cashweb.<br>
Verwachte waarden: 'AWC', 'AFC', 'ACC' of de betreffende codes.
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ═══ % Triple LOB ═════════════════════════════════════════
    st.markdown("## 🔗 % Triple LOB")

    onduidelijk_box("""
    <b>Triple LOB = klant heeft omzet in AWC + AFC + ACC tegelijk.</b><br>
    Huidige logica: relation_number met mutaties in ≥ 3 verschillende sub_administrations.<br>
    <b>Probleem:</b> als sub_administration niet consistent gevuld is, klopt deze telling niet.<br>
    <b>Actiepunt:</b> bevestig sub_administration vulling met Floor (zie debug hieronder).
    """)

    _df_triple = fetch(f"""
        SELECT
            relation_number,
            COUNT(DISTINCT sub_administration) AS aantal_lob,
            SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet,
            MIN(admin_code) AS admin_code
        FROM cashweb.ledger_mutations
        WHERE book_year = '{boekjaar}'
          AND journal_code IN {CW_OMZET_DAGBOEKEN}
          AND relation_number IS NOT NULL AND relation_number != ''
        GROUP BY relation_number
    """, "triple_lob")

    if not _df_triple.empty:
        _df_triple["omzet"] = _df_triple["omzet"].apply(safe_float)
        _n_all     = len(_df_triple)
        _n_triple  = len(_df_triple[_df_triple["aantal_lob"] >= 3])
        _n_double  = len(_df_triple[_df_triple["aantal_lob"] == 2])
        _n_single  = len(_df_triple[_df_triple["aantal_lob"] == 1])
        _omz_tri   = _df_triple[_df_triple["aantal_lob"] >= 3]["omzet"].sum()
        _omz_all   = _df_triple["omzet"].sum()
        _pct_kl    = (_n_triple / _n_all * 100)   if _n_all   > 0 else 0
        _pct_omz   = (_omz_tri  / _omz_all * 100) if _omz_all > 0 else 0

        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        col_t1.metric("Triple LOB klanten", str(_n_triple), f"Van {_n_all} totaal",
                      help=f"📌 DEFINITIE\n"
                           f"Triple LOB klant = een relatie die bij ALLE drie entiteiten (AWC + AFC + ACC)\n"
                           f"omzet heeft gegenereerd in het geselecteerde boekjaar.\n"
                           f"\n"
                           f"📐 FORMULE\n"
                           f"COUNT(relation_number)\n"
                           f"WHERE COUNT(DISTINCT admin_code) >= {_n_admins}\n"
                           f"AND journal_code IN ('50','VERK') [D-kant]\n"
                           f"\n"
                           f"🔢 RUWE BEREKENING\n"
                           f"Totaal unieke klanten: {_n_all}\n"
                           f"Klanten in 1 admin:    {_n_single}\n"
                           f"Klanten in 2 admins:   {_n_double}\n"
                           f"Klanten in 3 admins:   {_n_triple}  ← Triple LOB\n"
                           f"\n"
                           f"🗓️ FILTER\n"
                           f"book_year = '{boekjaar}' (heel jaar, niet per periode)\n"
                           f"Gevonden admin_codes: {_n_admins} (verwacht: 3)")
        col_t2.metric("% Triple LOB (klanten)", f"{_pct_kl:.1f}%",
                      help=f"📌 DEFINITIE\n"
                           f"Percentage van alle klanten dat bij alle drie entiteiten actief is.\n"
                           f"\n"
                           f"📐 FORMULE\n"
                           f"% Triple LOB = Triple LOB klanten / Totaal klanten × 100\n"
                           f"\n"
                           f"🔢 RUWE BEREKENING\n"
                           f"{_n_triple} / {_n_all} × 100 = {_pct_kl:.1f}%\n"
                           f"\n"
                           f"🗓️ FILTER\n"
                           f"book_year = '{boekjaar}' | journal_code IN ('50','VERK')")
        col_t3.metric("% Omzet via Triple LOB", f"{_pct_omz:.1f}%",
                      help=f"📌 DEFINITIE\n"
                           f"Het aandeel van de totale omzet dat afkomstig is van Triple LOB klanten.\n"
                           f"Strategisch doel: hoge % = bewijs van cross-sell succes tussen AWC/AFC/ACC.\n"
                           f"\n"
                           f"📐 FORMULE\n"
                           f"% Omzet Triple LOB = Omzet Triple LOB klanten / Totale omzet × 100\n"
                           f"\n"
                           f"🔢 RUWE BEREKENING\n"
                           f"Omzet Triple LOB: {fmt_eur(_omz_tri)}\n"
                           f"Totale omzet:     {fmt_eur(_omz_all)}\n"
                           f"{fmt_eur(_omz_tri)} / {fmt_eur(_omz_all)} × 100 = {_pct_omz:.1f}%\n"
                           f"\n"
                           f"🗓️ FILTER\n"
                           f"book_year = '{boekjaar}'")
        col_t4.metric("Double LOB klanten", str(_n_double),
              help=f"📌 DEFINITIE\n"
                   f"Klanten met omzet in precies 2 van de {_n_admins} administraties.\n"
                   f"Potentieel om nog een derde LOB aan toe te voegen.\n"
                   f"\n"
                   f"🔢 RUWE BEREKENING\n"
                   f"Double LOB ({_n_admins-1} van {_n_admins} admins): {_n_double}\n"
                   f"Single LOB (1 van {_n_admins} admins):  {_n_single}\n"
                   f"Triple LOB ({_n_admins} van {_n_admins} admins): {_n_triple}")

        with st.expander("🔍 Debug — Triple LOB detail"):
            _lob_dist = _df_triple.groupby("aantal_lob").agg(
                klanten=("relation_number","count"),
                omzet=("omzet","sum")
            ).reset_index()
            _lob_dist["omzet_fmt"] = _lob_dist["omzet"].apply(fmt_eur)
            st.markdown("**Verdeling klanten naar # LOB's:**")
            st.dataframe(_lob_dist[["aantal_lob","klanten","omzet_fmt"]], use_container_width=True, hide_index=True)
            st.markdown("**Top Triple LOB klanten:**")
            _top_tri = _df_triple[_df_triple["aantal_lob"]>=3].sort_values("omzet",ascending=False).head(15).copy()
            _top_tri["omzet_fmt"] = _top_tri["omzet"].apply(fmt_eur)
            st.dataframe(_top_tri[["relation_number","aantal_lob","omzet_fmt","admin_code"]],
                         use_container_width=True, hide_index=True)
            st.markdown("""
<div class="debug-box">
Triple LOB logica: relation_number heeft omzet in >= 3 sub_administrations<br>
in dagboek '50' of 'VERK' over het hele boekjaar (niet gefilterd op periode).<br><br>
⚠️ Als alle klanten '1 LOB' tonen, is sub_administration waarschijnlijk niet juist gevuld.<br>
⚠️ Controleer: zijn AWC/AFC/ACC als aparte sub_administrations zichtbaar?
</div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 3 — COMMERCIEEL (HubSpot)
# ════════════════════════════════════════════════════════════
with tab_com:
    st.markdown('<div class="kpi-badge blue">Commercieel — HubSpot</div>', unsafe_allow_html=True)
    st.subheader("Commerciële KPI's")
    st.caption(f"Databron: hubspot_v2 | Periode: {_start_datum} → {_eind_datum}")

    # ── Deals ophalen ────────────────────────────────────────
    _df_deals = fetch(f"""
        SELECT
            d.id, d.createdat, d.updatedat,
            d.dealstage, d.dealname, d.amount, d.closedate,
            ps.label AS stage_label,
            ps.metadata__isclosed AS is_gesloten,
            ps.metadata__probability AS kans
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.createdat >= '{_start_datum}' AND d.createdat <= '{_eind_datum}'
        ORDER BY d.createdat DESC
    """, "deals")

    _df_deals_v = fetch(f"""
        SELECT COUNT(*) AS n,
               SUM(CASE WHEN ps.metadata__isclosed='true'
                         AND CAST(COALESCE(d.amount,'0') AS FLOAT)>0 THEN 1 ELSE 0 END) AS won
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.createdat >= '{date(int(boekjaar)-1, maanden_filter[0], 1)}'
          AND d.createdat <= '{date(int(boekjaar)-1, _laatste_m,
                                    (date(int(boekjaar)-1, _laatste_m%12+1,1)-timedelta(days=1)).day
                                    if _laatste_m<12 else 31)}'
    """, "deals_v")

    # ═══ Win Rate ═════════════════════════════════════════════
    st.markdown("### 🏆 Win Rate (Conversion SQL → Customer)")

    if not _df_deals.empty:
        _df_deals["createdat"]   = pd.to_datetime(_df_deals["createdat"], utc=True, errors="coerce")
        _df_deals["amount_float"]= _df_deals["amount"].apply(lambda x: safe_float(x))
        _n_tot  = len(_df_deals)
        _n_won  = len(_df_deals[(_df_deals["is_gesloten"]=="true") & (_df_deals["amount_float"]>0)])
        _n_tot_v= int(_df_deals_v["n"].iloc[0])   if not _df_deals_v.empty else 0
        _n_won_v= int(_df_deals_v["won"].iloc[0])  if not _df_deals_v.empty else 0
        _wr     = _n_won / _n_tot * 100 if _n_tot > 0 else 0
        _wr_v   = _n_won_v / _n_tot_v * 100 if _n_tot_v > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Nieuwe Deals", str(_n_tot), delta=delta_tekst(_n_tot, _n_tot_v),
                    help=f"📌 DEFINITIE\n"
                         f"Aantal nieuwe deals aangemaakt in HubSpot in de geselecteerde periode.\n"
                         f"Een deal = een commerciële kans/offerte voor een prospect of klant.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"COUNT(id) FROM hubspot_v2.deals\n"
                         f"WHERE createdat BETWEEN start AND eind\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Huidig  ({_start_datum} → {_eind_datum}): {_n_tot} deals\n"
                         f"Vorig   (zelfde periode {int(boekjaar)-1}):     {_n_tot_v} deals\n"
                         f"Δ: {delta_tekst(_n_tot, _n_tot_v) or 'n.v.t.'}\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'\n"
                         f"JOIN: deals_pipeline__stages ON dealstage = id")
        col2.metric("Gewonnen Deals", str(_n_won),
                    help=f"📌 DEFINITIE\n"
                         f"Aantal deals in de geselecteerde periode met een 'gewonnen' status.\n"
                         f"Een deal is gewonnen als: stage is gesloten (isclosed=true) EN amount > 0.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"COUNT(id) WHERE metadata__isclosed = 'true' AND amount > 0\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Gewonnen:      {_n_won} van {_n_tot} deals\n"
                         f"Niet gewonnen: {_n_tot - _n_won} deals\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'\n"
                         f"⚠️ AANNAME: 'gewonnen' = gesloten stage + amount > 0.\n"
                         f"Controleer in pipeline stages welke label = 'Closed Won'.")
        col3.metric("Win Rate", f"{_wr:.1f}%", delta=delta_tekst(_wr, _wr_v),
                    help=f"📌 DEFINITIE\n"
                         f"Win Rate = het percentage van alle nieuwe deals dat uiteindelijk gewonnen wordt.\n"
                         f"Geeft inzicht in de effectiviteit van het salesproces (SQL → klant).\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"Win Rate = Gewonnen deals / Totaal deals × 100\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Huidig: {_n_won} / {_n_tot} × 100 = {_wr:.1f}%\n"
                         f"Vorig:  {_n_won_v} / {_n_tot_v} × 100 = {_wr_v:.1f}%\n"
                         f"Δ: {delta_tekst(_wr, _wr_v) or 'n.v.t.'}\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'")

        if "stage_label" in _df_deals.columns:
            st.bar_chart(_df_deals["stage_label"].value_counts())

        with st.expander("🔍 Debug — Deals + pipeline stages"):
            st.dataframe(
                _df_deals[["id","createdat","dealname","stage_label","is_gesloten","amount","kans"]].head(30),
                use_container_width=True, hide_index=True
            )
            st.markdown("**Alle pipeline stages:**")
            _stages = fetch("SELECT id, label, metadata__isclosed, metadata__probability FROM hubspot_v2.deals_pipeline__stages ORDER BY displayorder", "stages")
            if not _stages.empty:
                st.dataframe(_stages, use_container_width=True, hide_index=True)
            dl_knop("Download deals data", _df_deals, "Win Rate / Deals",
                    "Gewonnen: metadata__isclosed='true' AND amount>0",
                    f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'",
                    f"deals_{_start_datum}_{_eind_datum}.csv",
                    extra_df=_stages if not _stages.empty else None,
                    extra_label="PIPELINE STAGES", key="dl_com_deals")
            st.markdown(f"""
<div class="debug-box">
Win Rate = deals met is_gesloten='true' AND amount>0 / totaal deals<br>
Huidig: {_n_won}/{_n_tot} = {_wr:.1f}%<br>
Vorig:  {_n_won_v}/{_n_tot_v} = {_wr_v:.1f}%<br><br>
⚠️ AANNAME: 'Gewonnen' = gesloten stage + amount > 0.<br>
Bevestig welke stage_label = 'Closed Won' vs 'Closed Lost' in de tabel hierboven.
</div>""", unsafe_allow_html=True)
    else:
        st.warning("Geen deals gevonden.")

    st.markdown("---")

    # ═══ ICP Interacties ══════════════════════════════════════
    st.markdown("### 🎯 ICP Interacties")

    onduidelijk_box("""
    <b>Welk HubSpot-veld markeert een contact/bedrijf als ICP?</b><br>
    HubSpot activity logs (calls, emails, meetings) zijn niet gevonden in het schema.<br>
    Beschikbare tabellen: deals, contacts, companies, tickets — geen 'activities' of 'engagements'.<br>
    <b>Proxy:</b> nieuwe deals per week als benadering van ICP-interacties.<br>
    <b>Actiepunt:</b> (1) definieer ICP-tag in HubSpot companies/contacts, (2) controleer of engagements gesynchroniseerd worden.
    """)

    _df_icp = fetch(f"""
        SELECT DATE_TRUNC('week', createdat) AS week, COUNT(*) AS deals
        FROM hubspot_v2.deals
        WHERE createdat >= '{_start_datum}' AND createdat <= '{_eind_datum}'
        GROUP BY week ORDER BY week
    """, "icp_proxy")
    if not _df_icp.empty:
        _df_icp["week"] = pd.to_datetime(_df_icp["week"], errors="coerce")
        st.line_chart(_df_icp.set_index("week")["deals"])
        st.caption("⚠️ Proxy: nieuwe deals per week. Echte ICP-interactie data ontbreekt nog.")

    st.markdown("---")

    # ═══ Churn ICP ════════════════════════════════════════════
    st.markdown("### 📉 Churn ICP Customers")

    onduidelijk_box("""
    <b>Churn vereist ICP-tag (zie boven) + definitie van 'vertrokken'.</b><br>
    Notitie Excel: "Aantal ingevulde cancellation forms, checken of hier een label voor aan te maken is in Hubspot."<br>
    <b>Proxy:</b> 'Closed Lost' deals.<br>
    <b>Actiepunt:</b> maak een 'Churned'/'Cancelled' deal-stage of formulier in HubSpot (Mark).
    """)

    _df_churn = fetch(f"""
        SELECT d.id, d.createdat, d.dealname, ps.label AS stage_label
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.createdat >= '{_start_datum}' AND d.createdat <= '{_eind_datum}'
          AND ps.metadata__isclosed = 'true'
          AND (CAST(COALESCE(d.amount,'0') AS FLOAT) = 0
               OR LOWER(ps.label) LIKE '%lost%' OR LOWER(ps.label) LIKE '%verloren%')
        ORDER BY d.createdat DESC
    """, "churn")

    _n_churn = len(_df_churn) if not _df_churn.empty else 0
    st.metric("Verloren Deals (churn proxy)", str(_n_churn),
              help=f"📌 DEFINITIE\n"
                   f"Proxy voor klantverloop: deals die 'verloren' zijn gegaan in de periode.\n"
                   f"Echte churn vereist een ICP-tag en cancellation-formulier in HubSpot.\n"
                   f"\n"
                   f"📐 FORMULE (proxy)\n"
                   f"COUNT deals WHERE:\n"
                   f"  metadata__isclosed = 'true'\n"
                   f"  AND (amount = 0 OR stage LIKE '%lost%' OR stage LIKE '%verloren%')\n"
                   f"\n"
                   f"🔢 RUWE BEREKENING\n"
                   f"Verloren deals in periode: {_n_churn}\n"
                   f"\n"
                   f"🗓️ FILTER\n"
                   f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'\n"
                   f"\n"
                   f"⚠️ ACTIEPUNT\n"
                   f"Maak een 'Churned' deal-stage of cancellation form in HubSpot (Mark).\n"
                   f"Dan pas is dit een echte churnmeting i.p.v. proxy.")
    if not _df_churn.empty:
        with st.expander("🔍 Debug — Churn deals"):
            st.dataframe(_df_churn,
                use_container_width=True, hide_index=True)
        dl_knop("Download churn data", _df_churn, "Churn (Closed Lost proxy)",
                "metadata__isclosed='true' AND (amount=0 OR stage LIKE '%lost%')",
                f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'",
                f"churn_{_start_datum}_{_eind_datum}.csv", key="dl_com_churn")

    st.markdown("---")

    # ═══ Time to Onboarding ═══════════════════════════════════
    st.markdown("### 🚀 Time to Onboarding")

    onduidelijk_box("""
    <b>Custom HubSpot-dataveld 'eerste operationele datum' bestaat nog niet.</b><br>
    Noot Excel: "Nu alleen AWC, na onboarding flow revisit opnieuw bekijken."<br>
    <b>Proxy:</b> deal aangemaakt → deal gesloten (niet hetzelfde als contractdatum → eerste activiteit).<br>
    <b>Actiepunt:</b> voeg custom property 'onboarding_startdatum' toe in HubSpot (Mark).
    """)

    _df_onb = fetch(f"""
        SELECT d.id, d.createdat, d.closedate, d.dealname, ps.label AS stage_label
        FROM hubspot_v2.deals d
        LEFT JOIN hubspot_v2.deals_pipeline__stages ps ON d.dealstage = ps.id
        WHERE d.closedate >= '{_start_datum}' AND d.closedate <= '{_eind_datum}'
          AND ps.metadata__isclosed = 'true'
          AND CAST(COALESCE(d.amount,'0') AS FLOAT) > 0
    """, "onboarding")

    if not _df_onb.empty:
        _df_onb["createdat"] = pd.to_datetime(_df_onb["createdat"], utc=True, errors="coerce")
        _df_onb["closedate"] = pd.to_datetime(_df_onb["closedate"], utc=True, errors="coerce")
        _df_onb["dagen"]     = (_df_onb["closedate"] - _df_onb["createdat"]).dt.days
        _df_onb = _df_onb[_df_onb["dagen"] >= 0]
        if not _df_onb.empty:
            col_o1, col_o2 = st.columns(2)
            col_o1.metric("Gem. Time-to-Close (proxy)", f"{_df_onb['dagen'].mean():.0f} dagen",
                          help=f"📌 DEFINITIE\n"
                               f"Gemiddeld aantal dagen van deal aangemaakt → deal gesloten.\n"
                               f"Proxy voor Time to Onboarding (echte meting vereist custom datumveld).\n"
                               f"\n"
                               f"📐 FORMULE\n"
                               f"AVG(closedate − createdat) in dagen\n"
                               f"WHERE isclosed = 'true' AND amount > 0\n"
                               f"\n"
                               f"🔢 RUWE BEREKENING\n"
                               f"Gewonnen deals in periode: {len(_df_onb) if not _df_onb.empty else 0}\n"
                               f"Gem. doorlooptijd: {_df_onb['dagen'].mean():.0f} dagen\n"
                               f"Mediaan:           {_df_onb['dagen'].median():.0f} dagen\n"
                               f"Min/Max:           {_df_onb['dagen'].min():.0f} / {_df_onb['dagen'].max():.0f} dagen\n"
                               f"\n"
                               f"⚠️ PROXY — niet hetzelfde als echte onboarding\n"
                               f"Echte meting = contractdatum → eerste operationele activiteit\n"
                               f"Actiepunt: voeg custom HubSpot-veld 'onboarding_startdatum' toe (Mark).")
            col_o2.metric("Mediaan", f"{_df_onb['dagen'].median():.0f} dagen",
                          help=f"📌 DEFINITIE\n"
                               f"Mediaan doorlooptijd = de middelste waarde als alle deals op volgorde staan.\n"
                               f"Mediaan is robuuster dan gemiddelde: één deal van 200 dagen\n"
                               f"vertekent het gemiddelde, maar niet de mediaan.\n"
                               f"\n"
                               f"📐 FORMULE\n"
                               f"MEDIAN(closedate − createdat) in dagen\n"
                               f"\n"
                               f"🔢 RUWE BEREKENING\n"
                               f"Mediaan: {_df_onb['dagen'].median():.0f} dagen\n"
                               f"Gem.:    {_df_onb['dagen'].mean():.0f} dagen\n"
                               f"Verschil gem./mediaan geeft aan of er uitschieters zijn.")
            with st.expander("🔍 Debug — Onboarding proxy data"):
                st.dataframe(_df_onb[["dealname","createdat","closedate","dagen"]].head(20),
                             use_container_width=True, hide_index=True)
            dl_knop("Download onboarding data",
                    _df_onb[["dealname","createdat","closedate","dagen","stage_label"]],
                    "Time to Onboarding",
                    "AVG/MEDIAN(closedate - createdat) in dagen",
                    f"closedate BETWEEN '{_start_datum}' AND '{_eind_datum}'",
                    f"onboarding_{_start_datum}_{_eind_datum}.csv", key="dl_com_onb")
    else:
        st.info("Geen gesloten deals in deze periode voor onboarding berekening.")


# ════════════════════════════════════════════════════════════
# TAB 4 — AFC (Sprinter3000)
# ════════════════════════════════════════════════════════════
with tab_afc:
    st.markdown('<div class="kpi-badge green">AFC — Sprinter3000</div>', unsafe_allow_html=True)
    st.subheader("AFC Operationele KPI's")
    st.caption(f"Databron: sprinter3000 | Periode: {_start_datum} → {_eind_datum}")

    # ═══ Zendingen overzicht ══════════════════════════════════
    st.markdown("### 📦 Zendingen & Marge")

    if not _df_ship.empty:
        _n_s     = len(_df_ship)
        _tot_gpm = _df_ship["total_gpm_amount"].sum()
        _gem_gpm = _df_ship["total_gpm_amount"].mean()
        _tot_omz = _df_ship["total_sales_amount"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("# Zendingen", str(_n_s), delta=delta_tekst(_n_s, _n_ship_v),
                    help=f"📌 DEFINITIE\n"
                         f"Totaal aantal transportzendingen uitgevoerd door AFC in de periode.\n"
                         f"Elke unieke shipment_id in Sprinter = één zending.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"COUNT(shipment_id) FROM sprinter3000.shipments\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Huidig  ({_start_datum} → {_eind_datum}): {_n_ship}\n"
                         f"Vorig   (zelfde periode {int(boekjaar)-1}):    {_n_ship_v:.0f}\n"
                         f"Δ: {delta_tekst(_n_ship, _n_ship_v) or 'n.v.t.'}\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'")
        col2.metric("Totale Omzet", fmt_eur(_tot_omz),
                    help=f"📌 DEFINITIE\n"
                         f"Totale verkoopomzet AFC = som van alle gefactureerde verkoopbedragen.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"SUM(total_sales_amount) FROM sprinter3000.shipments\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"SUM({_n_ship} zendingen) = {fmt_eur(_tot_omz)}\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'\n"
                         f"⚠️ Dit is de verkoopprijs — niet de winstmarge. Zie GPM voor marge.")
        col3.metric("Totale Marge (GPM)", fmt_eur(_tot_gpm), delta=delta_tekst(_tot_gpm, _marge_v),
                    help=f"📌 DEFINITIE\n"
                         f"Totale bruto winstmarge AFC (GPM = Gross Profit Margin).\n"
                         f"GPM = verkoopprijs min inkoopprijs per zending, berekend door Sprinter.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"SUM(total_gpm_amount)\n"
                         f"waarbij: total_gpm_amount = total_sales_amount − total_purchase_amount\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Totale omzet:   {fmt_eur(_tot_omz)}\n"
                         f"Totale GPM:     {fmt_eur(_tot_gpm)}\n"
                         f"GPM marge %:    {(_tot_gpm/_tot_omz*100) if _tot_omz>0 else 0:.1f}%\n"
                         f"Vorige periode: {fmt_eur(_marge_v)}\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'")
        col4.metric("Gem. Marge / Zending", fmt_eur(_gem_gpm),
                    help=f"📌 DEFINITIE\n"
                         f"Gemiddelde bruto winstmarge per individuele zending.\n"
                         f"Hogere waarde = winstgevendere mix van zendingen.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"Gem. GPM/Zending = SUM(total_gpm_amount) / COUNT(shipment_id)\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"{fmt_eur(_tot_gpm)} / {_n_s} zendingen = {fmt_eur(_gem_gpm)}\n"
                         f"Spreiding: zie download voor GPM per klant en per zending.\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'")

        _df_ship["week"] = _df_ship["report_date"].dt.to_period("W").astype(str)
        _wt = _df_ship.groupby("week").agg(n=("shipment_id","count"), gpm=("total_gpm_amount","sum")).reset_index()
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown("**# Zendingen per week:**")
            st.bar_chart(_wt.set_index("week")["n"])
        with col_w2:
            st.markdown("**Marge (GPM) per week:**")
            st.line_chart(_wt.set_index("week")["gpm"])

        dl_knop("Download zendingen", _df_ship[[
                    "shipment_number","report_date","shipment_mode","shipment_status_code",
                    "klant_naam","total_sales_amount","total_purchase_amount","total_gpm_amount"]],
                "Zendingen & Marge (AFC)",
                "SUM(total_gpm_amount), COUNT(shipment_id)",
                f"report_date BETWEEN '{_start_datum}' AND '{_eind_datum}'",
                f"afc_zendingen_{_start_datum}_{_eind_datum}.csv", key="dl_afc_ship")

        with st.expander("🔍 Debug — Sprinter zendingen detail"):
            st.dataframe(
                _df_ship[["shipment_number","report_date","shipment_mode","shipment_status_code",
                           "klant_naam","total_sales_amount","total_gpm_amount"]].head(40),
                use_container_width=True, hide_index=True
            )
            st.markdown(f"""
<div class="debug-box">
Kolommen gebruikt:<br>
  report_date:            datum filter (rapportagedatum)<br>
  total_sales_amount:     verkoopbedrag (omzet)<br>
  total_purchase_amount:  inkoopbedrag<br>
  total_gpm_amount:       bruto winstmarge (sales − purchase, berekend door Sprinter)<br><br>
Totalen:<br>
  Zendingen: {_n_s}<br>
  Omzet:     {fmt_eur(_tot_omz)}<br>
  GPM:       {fmt_eur(_tot_gpm)}<br><br>
⚠️ report_date = rapportagedatum — niet per se verzenddatum of factuurdatum.<br>
Controleer of dit de juiste datumkolom is.
</div>""", unsafe_allow_html=True)

    else:
        st.warning("Geen Sprinter-data gevonden voor deze periode.")

    st.markdown("---")

    # ═══ Marge per klant ══════════════════════════════════════
    st.markdown("### 💼 Marge per Shipment — Top Klanten")

    if not _df_ship.empty:
        _df_klant = _df_ship.groupby("klant_naam").agg(
            zendingen=("shipment_id","count"),
            omzet=("total_sales_amount","sum"),
            gpm=("total_gpm_amount","sum")
        ).reset_index()
        _df_klant["mpz"] = _df_klant["gpm"] / _df_klant["zendingen"]
        _df_klant = _df_klant.sort_values("gpm", ascending=False).head(15)
        _df_klant["omzet_f"] = _df_klant["omzet"].apply(fmt_eur)
        _df_klant["gpm_f"]   = _df_klant["gpm"].apply(fmt_eur)
        _df_klant["mpz_f"]   = _df_klant["mpz"].apply(fmt_eur)
        st.dataframe(
            _df_klant[["klant_naam","zendingen","omzet_f","gpm_f","mpz_f"]].rename(columns={
                "klant_naam":"Klant","zendingen":"# Zendingen",
                "omzet_f":"Omzet","gpm_f":"Totale Marge","mpz_f":"Marge/Zending"
            }),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")

    # ═══ On-Time Delivery — PLACEHOLDER ═════════════════════
    st.markdown("### ⏱️ On-Time Delivery")

    info_box("""
    <b>On-Time Delivery is nog niet geïmplementeerd.</b><br>
    Reden: het is onduidelijk welk veld in Sprinter de <i>geplande</i> leveringsdatum bevat.<br>
    <code>report_date</code> is de rapportagedatum, niet de afgesproken leverdatum.<br>
    <b>Actiepunt (Floor):</b> bevestig welk veld in Sprinter3000 de afgesproken leveringsdatum is
    (bijv. <code>eta</code>, <code>etd</code>, <code>agreed_delivery_date</code>).<br>
    Dan implementeren we de formule: <code>(Op tijd geleverd / Totaal) × 100%</code>
    """)

    st.markdown("**Shipment status verdeling (ter referentie):**")
    if not _df_ship.empty:
        _st_dist = _df_ship["shipment_status_code"].value_counts().reset_index()
        _st_dist.columns = ["Status", "Aantal"]
        st.dataframe(_st_dist, use_container_width=True, hide_index=True)

        with st.expander("🔍 Debug — Sprinter schema (beschikbare datumkolommen)"):
            st.code("""
Beschikbare kolommen in sprinter3000.shipments:
  report_date         ← gebruikt als filter (rapportagedatum)
  shipment_status     ← numerieke status code
  shipment_status_code← status als text
  external_reference  ← externe ref
  quotation_id        ← link naar offerte

Niet gevonden in schema (maar mogelijk aanwezig bij draaien):
  eta, etd, agreed_delivery_date, actual_delivery_date

→ Vraag Floor welk veld de afgesproken leverdatum is.
            """, language="text")

    st.markdown("---")

    # ═══ Sprinter diagnostics ════════════════════════════════
    with st.expander("🔍 Debug — Sprinter shipment modes"):
        _df_modes = fetch(f"""
            SELECT shipment_mode, COUNT(*) AS n, AVG(total_gpm_amount) AS gem_gpm
            FROM sprinter3000.shipments
            WHERE report_date >= '{_start_datum}' AND report_date <= '{_eind_datum}'
            GROUP BY shipment_mode ORDER BY n DESC
        """, "modes")
        if not _df_modes.empty:
            st.dataframe(_df_modes, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# TAB 5 — MENSEN & HR
# ════════════════════════════════════════════════════════════
with tab_mensen:
    st.markdown('<div class="kpi-badge red">Mensen & HR</div>', unsafe_allow_html=True)
    st.subheader("People KPI's — AWC · AFC · ACC")

    # ═══ FTE via SAL-dagboek (Cashweb) ════════════════════════
    st.markdown("### 👷 FTE — Loonkosten via Cashweb (SAL dagboek)")

    info_box("""
    Hooray is nog niet verbonden. Als tijdelijke proxy gebruiken we het SAL-dagboek in Cashweb:<br>
    loonkosten per periode + aantal unieke relaties als benadering van medewerkercount.
    """)

    if not _df_sal.empty:
        _df_sal["loon_debet"]  = _df_sal["loon_debet"].apply(safe_float)
        _df_sal["loon_credit"] = _df_sal["loon_credit"].apply(safe_float)

        _loon_per_admin = _df_sal.groupby("admin_code").agg(
            loon_totaal=("loon_debet","sum"),
            periodes=("book_period","nunique"),
            unieke_relaties=("unieke_relaties","sum")
        ).reset_index()

        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Totale Loonkosten (SAL)", fmt_eur(_loon_totaal),
                      help=f"📌 DEFINITIE\n"
                           f"Totale loonkosten geboekt in dagboek SAL (salarissen).\n"
                           f"D-kant van SAL = nettoloon + loonheffing betaald aan medewerkers/fiscus.\n"
                           f"\n"
                           f"📐 FORMULE\n"
                           f"SUM(amount) WHERE debit_credit IN ('D','DEBET','DEBIT')\n"
                           f"AND journal_code = 'SAL'\n"
                           f"\n"
                           f"🔢 RUWE BEREKENING\n"
                           f"Loonkosten ({_periode_label}): {fmt_eur(_loon_totaal)}\n"
                           f"Periodes met SAL-boekingen: {_df_sal['book_period'].nunique() if not _df_sal.empty else 0}\n"
                           f"\n"
                           f"🗓️ FILTER\n"
                           f"book_year = '{boekjaar}' | book_period IN ({_bp_str})\n"
                           f"\n"
                           f"⚠️ AANNAME\n"
                           f"SAL-dagboek in AWC had 230 regels in 2025 (screenshot).\n"
                           f"C-kant = bank of te betalen lonen (tegenrekening) — niet meetellen.")
        col_s2.metric("Periodes met salarisboekingen", str(_df_sal["book_period"].nunique()),
                      help=f"📌 DEFINITIE\n"
                           f"Aantal periodes (maanden) waarin een salarisboeking is gedaan.\n"
                           f"Verwacht: elke maand 1 salarisboeking. Minder = ontbrekende maanden.\n"
                           f"\n"
                           f"📐 FORMULE\n"
                           f"COUNT(DISTINCT book_period) WHERE journal_code = 'SAL'\n"
                           f"\n"
                           f"🔢 RUWE BEREKENING\n"
                           f"Gevonden periodes: {_df_sal['book_period'].nunique() if not _df_sal.empty else 0}\n"
                           f"Geselecteerde periodes: {len(maanden_filter)}\n"
                           f"\n"
                           f"🗓️ FILTER\n"
                           f"book_year = '{boekjaar}' | book_period IN ({_bp_str})")
        col_s3.metric("Unieke relaties in SAL", str(_df_sal["unieke_relaties"].sum()),
                      help=f"📌 DEFINITIE\n"
                           f"Aantal unieke relaties in het SAL-dagboek als proxy voor personeelscount.\n"
                           f"In Cashweb = soms één relation_number per medewerker, soms samengevoegd.\n"
                           f"\n"
                           f"📐 FORMULE\n"
                           f"SUM(COUNT(DISTINCT relation_number) per periode) WHERE journal_code='SAL'\n"
                           f"\n"
                           f"🔢 RUWE BEREKENING\n"
                           f"Gevonden: {_df_sal['unieke_relaties'].sum() if not _df_sal.empty else 0} relaties\n"
                           f"\n"
                           f"⚠️ AANNAME / ONZEKERHEID\n"
                           f"relation_number in SAL ≠ per se één werknemer.\n"
                           f"Kan ook loonheffingsnummer of kostenplaats zijn.\n"
                           f"Verbind Hooray voor exacte FTE-count (Mira).")

        st.markdown("**Loonkosten per admin per periode:**")
        _df_sal["book_period_int"] = pd.to_numeric(_df_sal["book_period"], errors="coerce")
        _df_sal["maand"] = (_df_sal["book_period_int"] % 100).astype(int, errors="ignore").map(MAAND_NAMEN).fillna(_df_sal["book_period"].astype(str))
        st.bar_chart(_df_sal.groupby(["maand","admin_code"])["loon_debet"].sum().unstack(fill_value=0))

        with st.expander("🔍 Debug — SAL dagboek detail + FTE-proxy redenering"):
            st.dataframe(_df_sal, use_container_width=True, hide_index=True)
            st.markdown(f"""
<div class="debug-box">
SAL-dagboek logica:<br>
  journal_code = 'SAL' → salarisboeking<br>
  D-kant (debet): netto loonbetaling aan medewerker/loonheffing<br>
  C-kant (credit): bank of te betalen lonen (tegenrekening)<br><br>
FTE-proxy opties:<br>
  1. Loonkosten / gem. jaarsalaris (bijv. €45K) = ruwe FTE schatting<br>
     → {_loon_totaal:,.0f} / 45000 = ~{_loon_totaal/45000:.1f} FTE (aanname €45K/jr)<br>
  2. Aantal unieke relaties in SAL als bovengrens FTE<br><br>
⚠️ Loonboeking in Cashweb is een netto-betaling, geen volledig salarisoverzicht.<br>
   Werkgeverslasten (pensioenpremie, ZW, etc.) staan mogelijk apart.<br>
⚠️ Verbind Hooray voor exacte FTE-data (Mira/Mark).
</div>""", unsafe_allow_html=True)

        # FTE slider op basis van SAL-proxy
        _gem_sal_aanname = st.slider("Aangenomen gem. jaarsalaris per FTE (€)", 30000, 80000, 45000, 5000, key="sal_slider")
        _fte_sal_proxy   = (_loon_totaal * 12 / len(maanden_filter)) / _gem_sal_aanname if _gem_sal_aanname > 0 else 0
        _marge_per_fte   = _brutomarge / _fte_sal_proxy if _fte_sal_proxy > 0 else 0

        col_fte1, col_fte2, col_fte3 = st.columns(3)
        col_fte1.metric("FTE (SAL-proxy)", f"~{_fte_sal_proxy:.0f}",
                        help=f"📌 DEFINITIE\n"
                             f"Geschat aantal FTE op basis van loonkosten in SAL-dagboek.\n"
                             f"Proxy omdat Hooray nog niet verbonden is.\n"
                             f"\n"
                             f"📐 FORMULE\n"
                             f"FTE = (Loonkosten × 12 / periodes) / Aangenomen jaarsalaris\n"
                             f"\n"
                             f"🔢 RUWE BEREKENING\n"
                             f"Loonkosten in {len(maanden_filter)} periode(s): {fmt_eur(_loon_totaal)}\n"
                             f"Jaarbasis:  {fmt_eur(_loon_totaal * 12 / len(maanden_filter))}\n"
                             f"÷ €{_gem_sal_aanname:,} aanname = ~{_fte_sal_proxy:.1f} FTE\n"
                             f"\n"
                             f"⚠️ AANNAMES\n"
                             f"• Jaarsalaris per FTE: €{_gem_sal_aanname:,} (instelbaar via slider)\n"
                             f"• SAL-dagboek dekt alle medewerkers\n"
                             f"• Werkgeverslasten mogelijk apart geboekt")
        col_fte2.metric("Brutomarge (Cashweb)", fmt_eur(_brutomarge),
                        help=f"📌 DEFINITIE\n"
                             f"Brutomarge uit Cashweb, gebruikt als teller voor Bruto Margin/FTE.\n"
                             f"\n"
                             f"📐 FORMULE\n"
                             f"Brutomarge = Omzet (50/VERK D-kant) − Inkoop (INK C-kant)\n"
                             f"\n"
                             f"🔢 RUWE BEREKENING\n"
                             f"{fmt_eur(_totaal_omzet)} − {fmt_eur(_totaal_inkoop)} = {fmt_eur(_brutomarge)}\n"
                             f"\n"
                             f"🗓️ FILTER\n"
                             f"book_year='{boekjaar}' | book_period IN ({_bp_str})")
        col_fte3.metric("Bruto Margin / FTE", fmt_eur(_marge_per_fte),
                        help=f"📌 DEFINITIE\n"
                             f"Brutomarge gedeeld door het aantal FTE. Meet productiviteit.\n"
                             f"Hogere waarde = meer marge per medewerker = efficiëntere organisatie.\n"
                             f"\n"
                             f"📐 FORMULE\n"
                             f"Bruto Margin/FTE = Brutomarge (Cashweb) / FTE (SAL-proxy)\n"
                             f"\n"
                             f"🔢 RUWE BEREKENING\n"
                             f"Brutomarge: {fmt_eur(_brutomarge)}\n"
                             f"FTE-proxy:  ~{_fte_sal_proxy:.1f}\n"
                             f"Resultaat:  {fmt_eur(_brutomarge)} / {_fte_sal_proxy:.1f} = {fmt_eur(_marge_per_fte)}\n"
                             f"\n"
                             f"⚠️ BETROUWBAARHEID\n"
                             f"FTE is een schatting — verbind Hooray voor exacte waarde (Mira).\n"
                             f"Jaarsalaris-aanname: €{_gem_sal_aanname:,} (instelbaar via slider).")

        dl_knop("Download SAL/lonen data", _df_sal, "FTE proxy via SAL dagboek",
                "SUM(amount D-kant) WHERE journal_code='SAL'",
                f"book_year='{boekjaar}' AND book_period IN ({_bp_str})",
                f"sal_lonen_{boekjaar}.csv", key="dl_men_sal")
    else:
        st.warning("Geen SAL-dagboek data gevonden. Controleer of dagboek 'SAL' bestaat in Cashweb voor deze periode.")
        todo_box("Controleer dagboeken-tab (Samenvatting → debug) voor exacte dagboek-codes. SAL heeft 230 regels in 2025 (AWC screenshot).")

    st.markdown("---")

    # ═══ A/B Players ══════════════════════════════════════════
    st.markdown("### 🏅 A/B Players")

    st.markdown("""
    <div class="onduidelijk-box">
    ⚠️ <b>Nog toe te voegen in de app / HubSpot:</b><br>
    A/B Player classificatie is een handmatig proces (halfjaarlijks, via Excel/VIE People).<br>
    Er is nog geen automatische databron beschikbaar.<br><br>
    <b>Opties om dit te structureren:</b><br>
    1. Upload resultaten halfjaarlijkse evaluatie als CSV → integreer in dit dashboard<br>
    2. Registreer A/B/C-classificatie als custom property in HubSpot (contacts) → automatisch leesbaar<br>
    3. Koppel VIE People API wanneer beschikbaar<br><br>
    <b>Verantwoordelijke:</b> Mark | <b>Frequentie:</b> Halfjaarlijks
    </div>""", unsafe_allow_html=True)

    col_ab1, col_ab2, col_ab3 = st.columns(3)
    with col_ab1:
        _ab_a = st.number_input("# A Players", min_value=0, value=0, key="ab_a")
    with col_ab2:
        _ab_b = st.number_input("# B Players", min_value=0, value=0, key="ab_b")
    with col_ab3:
        _ab_c = st.number_input("# C Players", min_value=0, value=0, key="ab_c")
    _tot_ab = _ab_a + _ab_b + _ab_c
    if _tot_ab > 0:
        st.metric("% A/B Players", f"{(_ab_a+_ab_b)/_tot_ab*100:.0f}%")

    st.markdown("---")

    # ═══ eNPS ════════════════════════════════════════════════
    st.markdown("### 📊 eNPS (Employee Net Promoter Score)")

    st.markdown("""
    <div class="onduidelijk-box">
    ⚠️ <b>Nog toe te voegen in de app / Microsoft Forms:</b><br>
    eNPS wordt gemeten via een periodiek medewerkersonderzoek.<br>
    Microsoft Forms is nog niet verbonden aan Peliqan — handmatige input als tijdelijk alternatief.<br><br>
    <b>Stappen om te automatiseren:</b><br>
    1. Maak een terugkerende Microsoft Forms-enquête (maandelijks) → schakel in via VIE People<br>
    2. Verbind Microsoft Forms aan Peliqan (connector beschikbaar: Microsoft 365)<br>
    3. Lees form_responses uit → bereken % Promoters (9-10) − % Detractors (0-6)<br><br>
    <b>Verantwoordelijke:</b> Mira | <b>Frequentie:</b> Maandelijks
    </div>""", unsafe_allow_html=True)

    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        _ep = st.slider("% Promoters (handmatig)", 0, 100, 50, key="ep")
    with col_e2:
        _ed = st.slider("% Detractors (handmatig)", 0, 100-_ep, 10, key="ed")
    _enps_score = _ep - _ed
    col_e3.metric("eNPS Score", str(_enps_score))

    st.markdown("---")

    # ═══ Intern vs Extern ═════════════════════════════════════
    st.markdown("### ⚖️ Intern vs. Extern")

    st.markdown("""
    <div class="onduidelijk-box">
    ⚠️ <b>Nog toe te voegen via Hooray:</b><br>
    Verhouding vast personeel vs. ingehuurde krachten komt uit het HR-systeem Hooray.<br>
    Hooray is nog niet verbonden aan Peliqan.<br><br>
    <b>Alternatief:</b> SAL dagboek in Cashweb geeft inzicht in loonkosten, maar geen verdeling vast/flex.<br>
    <b>Stappen:</b><br>
    1. Verbind Hooray aan Peliqan (HR REST API of Peliqan native connector)<br>
    2. Lees medewerkercontract-types uit (vast/flex/oproep/uitzend)<br>
    3. Bereken verhouding per entiteit (AWC/AFC/ACC)<br><br>
    <b>Verantwoordelijke:</b> Mira | <b>Frequentie:</b> Maandelijks
    </div>""", unsafe_allow_html=True)

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        _intern = st.number_input("# Vast (handmatig)", min_value=0, value=20, key="intern")
    with col_i2:
        _extern = st.number_input("# Inleen/flex (handmatig)", min_value=0, value=10, key="extern")
    _tot_ft = _intern + _extern
    if _tot_ft > 0:
        col_i3, col_i4 = st.columns(2)
        col_i3.metric("% Intern", f"{_intern/_tot_ft*100:.0f}%")
        col_i4.metric("Totaal FTE", str(_tot_ft))


# ════════════════════════════════════════════════════════════
# TAB 6 — TICKETS & NPS
# ════════════════════════════════════════════════════════════
with tab_tickets:
    st.markdown('<div class="kpi-badge">Tickets & NPS — HubSpot</div>', unsafe_allow_html=True)
    st.subheader("Customer Service & NPS")
    st.caption(f"Databron: hubspot_v2 | Periode: {_start_datum} → {_eind_datum}")

    # ── Tickets ──────────────────────────────────────────────
    _df_tick = fetch(f"""
        SELECT
            t.id, t.createdat, t.closed_date, t.subject,
            t.hs_ticket_priority, t.hs_pipeline, t.hs_pipeline_stage,
            t.category_issue, t.time_to_close, t.time_to_first_agent_reply,
            ps.label AS status_label
        FROM hubspot_v2.tickets t
        LEFT JOIN hubspot_v2.tickets_pipeline__stages ps ON t.hs_pipeline_stage = ps.id
        WHERE t.createdat >= '{_start_datum}' AND t.createdat <= '{_eind_datum}'
        ORDER BY t.createdat DESC
    """, "tickets")

    _df_tick_v = fetch(f"""
        SELECT COUNT(*) AS n FROM hubspot_v2.tickets
        WHERE createdat >= '{date(int(boekjaar)-1, maanden_filter[0], 1)}'
          AND createdat <= '{date(int(boekjaar)-1, _laatste_m,
                                  (date(int(boekjaar)-1, _laatste_m%12+1,1)-timedelta(days=1)).day
                                  if _laatste_m<12 else 31)}'
    """, "tickets_v")

    # ═══ Tickets metrics ══════════════════════════════════════
    st.markdown("### 🎫 Tickets")

    if not _df_tick.empty:
        _df_tick["createdat"]   = pd.to_datetime(_df_tick["createdat"],   utc=True, errors="coerce")
        _df_tick["closed_date"] = pd.to_datetime(_df_tick["closed_date"], utc=True, errors="coerce")
        _df_tick["time_to_close"] = pd.to_numeric(_df_tick["time_to_close"], errors="coerce")

        _n_t   = len(_df_tick)
        _n_op  = _df_tick["closed_date"].isna().sum()
        _n_cl  = _n_t - _n_op
        _n_t_v = int(_df_tick_v["n"].iloc[0]) if not _df_tick_v.empty else 0
        _ttc   = _df_tick["time_to_close"].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Totaal Tickets", str(_n_t), delta=delta_tekst(_n_t, _n_t_v),
                    help=f"📌 DEFINITIE\n"
                         f"Totaal aantal binnengekomen support-tickets in de periode.\n"
                         f"Tickets zijn e-mails/meldingen van klanten aan customer service.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"COUNT(id) FROM hubspot_v2.tickets\n"
                         f"WHERE createdat BETWEEN start AND eind\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Huidig  ({_start_datum} → {_eind_datum}): {_n_t}\n"
                         f"Vorig   (zelfde periode {int(boekjaar)-1}):     {_n_t_v}\n"
                         f"Open:     {_n_op} | Gesloten: {_n_cl}\n"
                         f"\n"
                         f"⚠️ SCOPE\n"
                         f"Tickets via HubSpot = AWC. Voor AFC en ACC is onduidelijk\n"
                         f"of tickets ook via HubSpot lopen.")
        col2.metric("Open", str(_n_op),
                    help=f"📌 DEFINITIE\n"
                         f"Tickets aangemaakt in de periode die nog niet gesloten zijn.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"COUNT(id) WHERE closed_date IS NULL\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Totaal: {_n_t} | Open: {_n_op} | = {(_n_op/_n_t*100) if _n_t>0 else 0:.0f}% openstaand\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'")
        col3.metric("Gesloten", str(_n_cl),
                    help=f"📌 DEFINITIE\n"
                         f"Tickets aangemaakt in de periode die inmiddels gesloten zijn.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"COUNT(id) WHERE closed_date IS NOT NULL\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Gesloten: {_n_cl} van {_n_t} = {(_n_cl/_n_t*100) if _n_t>0 else 0:.0f}% opgelost\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'")
        col4.metric("Gem. Time-to-Close",
                    f"{_ttc/60:.1f} uur" if pd.notna(_ttc) and _ttc > 60 else f"{_ttc:.0f} min" if pd.notna(_ttc) else "—",
                    help=f"📌 DEFINITIE\n"
                         f"Gemiddelde tijd van ticket aangemaakt → ticket gesloten.\n"
                         f"Maatstaf voor de snelheid van de customer service afdeling.\n"
                         f"\n"
                         f"📐 FORMULE\n"
                         f"AVG(time_to_close) in minuten → getoond in uren als > 60 min\n"
                         f"\n"
                         f"🔢 RUWE BEREKENING\n"
                         f"Gem. time_to_close: {_ttc:.0f} minuten = {_ttc/60:.1f} uur\n"
                         f"Gebaseerd op: {_n_cl} gesloten tickets\n"
                         f"\n"
                         f"🗓️ FILTER\n"
                         f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'\n"
                         f"⚠️ time_to_close = minuten zoals geregistreerd door HubSpot.")

        _df_tick["week"] = _df_tick["createdat"].dt.to_period("W").astype(str)
        st.line_chart(_df_tick.groupby("week").size())

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("**Per status:**")
            st.dataframe(_df_tick["status_label"].value_counts().reset_index().rename(
                columns={"index":"Status","status_label":"Status","count":"Aantal"}),
                use_container_width=True, hide_index=True)
        with col_t2:
            st.markdown("**Per prioriteit:**")
            st.dataframe(_df_tick["hs_ticket_priority"].value_counts().reset_index().rename(
                columns={"index":"Prioriteit","hs_ticket_priority":"Prioriteit","count":"Aantal"}),
                use_container_width=True, hide_index=True)

        dl_knop("Download ticket data", _df_tick[[
                    "id","createdat","closed_date","subject","status_label",
                    "hs_ticket_priority","category_issue","time_to_close","time_to_first_agent_reply"]],
                "Tickets",
                "COUNT, AVG(time_to_close)",
                f"createdat BETWEEN '{_start_datum}' AND '{_eind_datum}'",
                f"tickets_{_start_datum}_{_eind_datum}.csv", key="dl_tick")
        with st.expander("🔍 Debug — Ticket data (eerste 30 rijen)"):
            st.dataframe(
                _df_tick[["id","createdat","subject","status_label","hs_ticket_priority",
                           "category_issue","time_to_close","time_to_first_agent_reply"]].head(30),
                use_container_width=True, hide_index=True
            )
            st.markdown(f"""
<div class="debug-box">
Kolommen gebruikt (bevestigd werkend via referentie dashboard):<br>
  createdat, closed_date, subject, hs_ticket_priority, hs_pipeline,<br>
  hs_pipeline_stage, category_issue, time_to_close, time_to_first_agent_reply<br>
JOIN: tickets_pipeline__stages ON hs_pipeline_stage = ps.id → ps.label<br><br>
Totaal: {_n_t} | Open: {_n_op} | Gesloten: {_n_cl}<br>
Gem. Time-to-Close: {_ttc:.0f} minuten = {_ttc/60:.1f} uur<br><br>
⚠️ Voor AFC en ACC: onduidelijk of tickets ook via HubSpot lopen.<br>
   Notitie Excel: "Hubspot, voor AFC, ACC onduidelijk"
</div>""", unsafe_allow_html=True)
    else:
        st.warning("Geen tickets in deze periode.")

    st.markdown("---")

    # ═══ NPS ══════════════════════════════════════════════════
    st.markdown("### ⭐ NPS (Net Promoter Score)")

    st.markdown("""
    <div class="onduidelijk-box">
    ⚠️ <b>Nog toe te voegen in HubSpot Service Hub:</b><br>
    NPS wordt gemeten via <code>feedback_submissions</code> in HubSpot, maar de score-kolom is nog
    niet zichtbaar in het schema (alleen <code>id, createdat, archived, url</code>).<br><br>
    <b>Wat er nog moet gebeuren:</b><br>
    1. Activeer NPS-surveys in HubSpot Service Hub (als dit nog niet gedaan is)<br>
    2. Run in Peliqan: <code>pq.get_table(tabel_id)</code> op <code>feedback_submissions</code><br>
       → zoek naar velden als <code>nps_score</code>, <code>hs_survey_channel</code>, <code>hs_response_text</code><br>
    3. Zodra de score-kolom gevonden is, implementeer ik de NPS-berekening in dit dashboard<br><br>
    <b>NPS formule:</b> % Promoters (score 9-10) − % Detractors (score 0-6)<br>
    <b>Verantwoordelijke:</b> Mark | <b>Frequentie:</b> Maandelijks
    </div>""", unsafe_allow_html=True)

    # Toon wat er nu al in feedback_submissions zit
    _df_nps = fetch(f"""
        SELECT id, createdat, archived
        FROM hubspot_v2.feedback_submissions
        WHERE createdat >= '{_start_datum}' AND createdat <= '{_eind_datum}'
        ORDER BY createdat DESC LIMIT 100
    """, "nps")

    if not _df_nps.empty:
        st.metric("Feedback submissions gevonden", str(len(_df_nps)),
                  help="De tabel bestaat — score-kolom nog niet gevonden")
        with st.expander("🔍 Debug — feedback_submissions (welke kolommen zijn er?)"):
            st.dataframe(_df_nps.head(10), use_container_width=True, hide_index=True)
            st.markdown("**Kolomnamen gevonden:**")
            st.code(list(_df_nps.columns), language="python")
            st.markdown("""
<div class="debug-box">
De tabel feedback_submissions bestaat en bevat data.<br>
De NPS-score kolom is NIET zichtbaar via de standaard schema-export.<br><br>
Om verborgen HubSpot-kolommen te vinden, run in Peliqan console:<br>
  1. tables = pq.list_databases()[warehouse='dw_2401']<br>
  2. zoek tabel met name='feedback_submissions'<br>
  3. pq.get_table(tabel['id']) → meta.get('all_fields', [])<br><br>
Verwachte velden: nps_score (1-10), hs_survey_channel, hs_response_text,<br>
  hs_object_source, hs_created_by_user_id
</div>""", unsafe_allow_html=True)
    else:
        st.info("Geen NPS-data voor deze periode. Controleer of HubSpot Service Hub actief is en NPS-surveys verstuurd worden.")

    st.markdown("---")

    # ═══ LTV Triple LOB ═══════════════════════════════════════
    st.markdown("### 💎 Life Time Value — Triple LOB Klanten")

    onduidelijk_box("""
    <b>LTV-formule moet afgestemd worden met Floor.</b><br>
    Notitie Excel: "Calc sheet afstemmen met floor; geen inzicht"<br>
    <b>Definitie Triple LOB:</b> klant (relation_number) heeft omzet in <b>alle 3 de administraties</b>
    (AWC + AFC + ACC) in Cashweb — dus dezelfde relatie die bij alle drie entiteiten zakendoet.<br>
    Huidige proxy: cumulatieve omzet per triple-LOB klant over alle boekjaren.<br>
    Echte LTV formule (nog vast te stellen met Floor): (Gem. maandomzet × Marge%) / Maandelijkse churn rate.
    """)

    # Stap 1: admin count is al geladen in de gedeelde datasectie (_n_admins, _df_admins_vroeg)
    _df_admins_ltv = _df_admins_vroeg.copy()

    # Stap 2: per relation_number → in hoeveel unieke admin_codes heeft deze klant omzet?
    # Triple LOB = aanwezig in alle bekende admin_codes
    _df_ltv_all = fetch(f"""
        SELECT
            relation_number,
            admin_code,
            SUM(CASE WHEN {CW_IS_D} THEN {CW_AMOUNT} ELSE 0 END) AS omzet_admin
        FROM cashweb.ledger_mutations
        WHERE journal_code IN {CW_OMZET_DAGBOEKEN}
          AND relation_number IS NOT NULL AND relation_number != ''
          AND admin_code IS NOT NULL AND admin_code != ''
        GROUP BY relation_number, admin_code
    """, "ltv_per_admin")

    if not _df_ltv_all.empty:
        _df_ltv_all["omzet_admin"] = _df_ltv_all["omzet_admin"].apply(safe_float)

        # Groepeer per klant: tel hoeveel admins + totale omzet
        _df_ltv = _df_ltv_all.groupby("relation_number").agg(
            admin_codes=("admin_code", lambda x: sorted(x.unique().tolist())),
            aantal_admins=("admin_code", "nunique"),
            totale_omzet=("omzet_admin", "sum"),
        ).reset_index()

        # Triple LOB = klant in evenveel admins als er totaal zijn
        # (als er 3 admins zijn → alle 3 aanwezig; als er 2 zijn → beiden aanwezig)
        _df_ltv["is_triple"] = _df_ltv["aantal_admins"] >= max(_n_admins, 3)
        _df_triple_klanten   = _df_ltv[_df_ltv["is_triple"]].copy()
        _df_triple_klanten   = _df_triple_klanten.sort_values("totale_omzet", ascending=False)

        _n_triple        = len(_df_triple_klanten)
        _n_alle_klanten  = len(_df_ltv)
        _gem_ltv_triple  = _df_triple_klanten["totale_omzet"].mean() if _n_triple > 0 else 0
        _totaal_ltv_tri  = _df_triple_klanten["totale_omzet"].sum()
        _pct_triple_kl   = (_n_triple / _n_alle_klanten * 100) if _n_alle_klanten > 0 else 0

        # ── Hoofd-metrics: € groot bovenaan, count eronder ────
        col_ltv1, col_ltv2, col_ltv3 = st.columns(3)

        with col_ltv1:
            st.metric(
                "💶 Gem. LTV Triple LOB klant",
                fmt_eur(_gem_ltv_triple),
                help=f"📌 DEFINITIE\n"
                     f"Gemiddelde Life Time Value van klanten die bij alle 3 entiteiten actief zijn.\n"
                     f"LTV proxy = cumulatieve omzet over alle boekjaren samen per klant.\n"
                     f"Geeft aan hoeveel een 'triple-klant' gemiddeld waard is over de hele relatie.\n"
                     f"\n"
                     f"📐 FORMULE\n"
                     f"AVG(cumulatieve omzet per relation_number)\n"
                     f"WHERE COUNT(DISTINCT admin_code) >= {_n_admins}\n"
                     f"Dagboek: '50' of 'VERK', D-kant | Periode: ALLE jaren\n"
                     f"\n"
                     f"🔢 RUWE BEREKENING\n"
                     f"Triple LOB klanten: {_n_triple}\n"
                     f"Totale omzet tezamen: {fmt_eur(_totaal_ltv_tri)}\n"
                     f"Gem. LTV: {fmt_eur(_totaal_ltv_tri)} / {_n_triple} = {fmt_eur(_gem_ltv_triple)}\n"
                     f"\n"
                     f"⚠️ PROXY — formule af te stemmen met Floor:\n"
                     f"Echte LTV = (Gem. maandomzet × Marge%) / Churn rate"
            )
            st.caption(f"📌 Op basis van **{_n_triple} klanten** met Triple LOB")

        with col_ltv2:
            st.metric(
                "💶 Totale omzet Triple LOB",
                fmt_eur(_totaal_ltv_tri),
                help=f"📌 DEFINITIE\n"
                     f"Totale cumulatieve omzet van alle triple-LOB klanten gecombineerd.\n"
                     f"\n"
                     f"📐 FORMULE\n"
                     f"SUM(omzet per relation_number) WHERE aanwezig in alle {_n_admins} admins\n"
                     f"\n"
                     f"🔢 RUWE BEREKENING\n"
                     f"Klanten in berekening: {_n_triple}\n"
                     f"Totale omzet: {fmt_eur(_totaal_ltv_tri)}\n"
                     f"= {_pct_triple_kl:.1f}% van alle {_n_alle_klanten} klanten\n"
                     f"\n"
                     f"⚠️ Sprinter-omzet (AFC) is NIET meegenomen — alleen Cashweb."
            )
            st.caption(f"📌 **{_pct_triple_kl:.1f}%** van alle {_n_alle_klanten} klanten")

        with col_ltv3:
            st.metric(
                "# Triple LOB klanten",
                str(_n_triple),
                help=f"📌 DEFINITIE\n"
                     f"Aantal unieke klanten (relaties) die bij ALLE drie entiteiten actief zijn.\n"
                     f"Gebaseerd op: relation_number aanwezig in alle gevonden admin_codes.\n"
                     f"\n"
                     f"📐 FORMULE\n"
                     f"COUNT(relation_number) WHERE COUNT(DISTINCT admin_code) >= {_n_admins}\n"
                     f"\n"
                     f"🔢 RUWE BEREKENING\n"
                     f"Totaal unieke klanten (met omzet): {_n_alle_klanten}\n"
                     f"Triple LOB (in alle {_n_admins} admins): {_n_triple}\n"
                     f"% Triple LOB: {_pct_triple_kl:.1f}%\n"
                     f"\n"
                     f"🗓️ FILTER\n"
                     f"Alle boekjaren (cumulatief) | journal_code IN ('50','VERK')\n"
                     f"Gevonden admins: {_n_admins} (verwacht: 3 — AWC + AFC + ACC)"
            )
            st.caption(f"📌 Admins gevonden: **{_n_admins}** (verwacht: 3)")

        # ── Tabel triple LOB klanten ───────────────────────────
        if _n_triple > 0:
            st.markdown("**Triple LOB klanten — omzet per klant (cumulatief alle boekjaren):**")
            _show_tri = _df_triple_klanten.copy()
            _show_tri["totale_omzet_fmt"] = _show_tri["totale_omzet"].apply(fmt_eur)
            _show_tri["admins"]           = _show_tri["admin_codes"].apply(lambda x: " · ".join(x))
            st.dataframe(
                _show_tri[["relation_number","admins","totale_omzet_fmt"]].rename(columns={
                    "relation_number": "Relatienummer",
                    "admins":          "Administraties",
                    "totale_omzet_fmt":"Cumulatieve Omzet (LTV proxy)",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(f"Geen klanten gevonden in alle {_n_admins} administraties tegelijk. "
                    "Mogelijke oorzaken: admin_code niet consistent, of er zijn minder dan 3 admins verbonden.")

        with st.expander("🔍 Debug — LTV Triple LOB berekening (stap voor stap)"):
            st.markdown("**Stap 1 — Unieke admin_codes in Cashweb:**")
            if not _df_admins_ltv.empty:
                st.dataframe(_df_admins_ltv, use_container_width=True, hide_index=True)

            st.markdown("**Stap 2 — Omzet per relation_number per admin (eerste 30 rijen):**")
            st.dataframe(_df_ltv_all.head(30), use_container_width=True, hide_index=True)

            st.markdown("**Stap 3 — Klanten geaggregeerd (aantal admins + totale omzet):**")
            _show_all = _df_ltv.copy()
            _show_all["totale_omzet_fmt"] = _show_all["totale_omzet"].apply(fmt_eur)
            _show_all["admins"] = _show_all["admin_codes"].apply(lambda x: " · ".join(x))
            dl_knop("Download Triple LOB analyse", _df_ltv_all, "Triple LOB",
                    "COUNT(DISTINCT admin_code) >= 3 per relation_number",
                    "journal_code IN ('50','VERK'), D-kant, ALLE boekjaren",
                    "triple_lob.csv",
                    extra_df=_df_triple_klanten if _n_triple > 0 else None,
                    extra_label="TRIPLE LOB KLANTEN", key="dl_fin_triple")
            st.dataframe(
                _show_all[["relation_number","admins","aantal_admins","totale_omzet_fmt","is_triple"]].sort_values("aantal_admins", ascending=False).head(30),
                use_container_width=True, hide_index=True
            )

            st.markdown(f"""
<div class="debug-box">
Logica Triple LOB (stap voor stap):<br>
  1. Haal alle admin_codes op → gevonden: {_n_admins} admins<br>
  2. Per relation_number: tel in hoeveel admins deze klant omzet heeft<br>
  3. Triple LOB = aanwezig in alle {_n_admins} admins (of ≥ 3 als er meer zijn)<br><br>
Omzet filter: dagboek '50' of 'VERK', D-kant (debiteurenboeking = factuurbedrag klant)<br>
Periode: ALLE boekjaren (geen jaar-filter) → cumulatieve LTV over de hele relatie<br><br>
Resultaat:<br>
  Totaal klanten met omzet: {_n_alle_klanten}<br>
  Triple LOB (in alle {_n_admins} admins): {_n_triple}<br>
  % Triple LOB: {_pct_triple_kl:.1f}%<br>
  Gem. LTV Triple LOB: {fmt_eur(_gem_ltv_triple)}<br><br>
⚠️ Als aantal_admins overal '1' is: admin_code niet consistent gevuld.<br>
⚠️ Als er < 3 admins gevonden worden: voeg ontbrekende admins toe in Peliqan connector.<br>
⚠️ Sprinter-omzet (AFC) is NIET meegenomen in deze berekening.
</div>""", unsafe_allow_html=True)

    else:
        st.warning("Geen Cashweb omzetdata beschikbaar voor LTV berekening.")
        with st.expander("🔍 Debug — LTV data check"):
            st.markdown("Controleer of dagboek '50' of 'VERK' bestaat en of relation_number gevuld is.")
            _df_ltv_check = fetch(f"""
                SELECT journal_code, COUNT(*) AS n,
                       COUNT(DISTINCT relation_number) AS unieke_relaties
                FROM cashweb.ledger_mutations
                WHERE journal_code IN {CW_OMZET_DAGBOEKEN}
                GROUP BY journal_code
            """, "ltv_check")
            if not _df_ltv_check.empty:
                st.dataframe(_df_ltv_check, use_container_width=True, hide_index=True)


# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#AAAAAA;font-size:0.72rem;"
    "letter-spacing:0.06em;text-transform:uppercase'>"
    "Amsterdam Companies &nbsp;·&nbsp; MT Dashboard v2 &nbsp;·&nbsp; "
    "Team Data · Peliqan + Streamlit · dw_2401"
    "</p>",
    unsafe_allow_html=True,
)