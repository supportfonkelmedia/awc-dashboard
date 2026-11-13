# Peliqan app 13737 (kpi_7t_naar_warehouse), live stand 2026-11-13: outbound_zendingen erbij. Vorige stand: ~/AWC/peliqan-backups/2026-11-13-app13737-voor-zendingen.py
from datetime import datetime, timezone
import statistics

VANAF = '2026-01-01'
DW = pq.DW_NAME
dw = pq.dbconnect(DW)
t7 = pq.dbconnect('7T')
nu = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def schrijf(stmt, label):
    # dbconn.execute kan {'status': 'failed'} teruggeven zonder te raisen: zelf controleren.
    res = dw.execute(DW, query=stmt)
    st.write(f"{label} write-resultaat: {str(res)[:300]}")
    if isinstance(res, dict):
        status = str(res.get('status', '')).lower()
        if status in ('failed', 'error') or res.get('error'):
            raise RuntimeError(f"{label}: schrijven mislukt: {res}")
    return res


def controleer(tabel, verwacht):
    # Telt de rijen die deze run echt heeft geschreven (geschreven_op = nu).
    r = dw.fetch(DW, query=f"SELECT COUNT(*) AS n FROM kpi_data.{tabel} WHERE geschreven_op = TIMESTAMPTZ '{nu}+00'")
    n = int(r[0]['n']) if r else 0
    if n != verwacht:
        raise RuntimeError(f"{tabel}: {n} rijen met geschreven_op={nu}, verwacht {verwacht}")
    st.write(f"{tabel}: {n} rijen geschreven (gecontroleerd)")


# ---------- 1. Dock-to-stock ----------
# Eindtijd = Datum van de eerste verplaatsing (Status 30): het moment van de verplaatsing zelf.
# (Was MIN(MutatieDatum): een laatst-gewijzigd-stempel, vaak uren later dan de verplaatsing.)
sql = f"""
SELECT FORMAT(s.Los_Datum, 'yyyy-MM') AS maand,
  DATEDIFF(MINUTE, s.Los_Datum, v.eerste_verpl) AS minuten,
  CASE WHEN v.so IS NULL AND w.so IS NOT NULL THEN 1 ELSE 0 END AS onderweg,
  CASE WHEN DATEDIFF(SECOND, s.AanmaakDatum, s.Los_Datum) = 0 THEN 1 ELSE 0 END AS los_is_aanmaak
FROM dbo.Spare_Orders s
LEFT JOIN (
  SELECT LTRIM(RTRIM(o.Spare_Order_ID)) AS so, MIN(v.Datum) AS eerste_verpl
  FROM dbo.Ontvangsten o JOIN dbo.Voorraad_Verplaatsingen v ON v.Ontvangst_ID = o.ID
  WHERE v.Status = 30
  GROUP BY LTRIM(RTRIM(o.Spare_Order_ID))
) v ON v.so = LTRIM(RTRIM(s.ID))
LEFT JOIN (
  SELECT DISTINCT LTRIM(RTRIM(o.Spare_Order_ID)) AS so
  FROM dbo.Ontvangsten o JOIN dbo.Voorraad_Verplaatsingen v ON v.Ontvangst_ID = o.ID
  WHERE v.Status IN (5, 25)
) w ON w.so = LTRIM(RTRIM(s.ID))
WHERE s.Gelost = 1 AND s.Los_Datum >= '{VANAF}'
"""
rows = t7.fetch('DB7T', query=sql)

per = {}
for r in rows:
    m = str(r['maand'])[:7]
    d = per.setdefault(m, {'inbounds': 0, 'min': [], 'onderweg': 0, 'los_is_aanmaak': 0})
    d['inbounds'] += 1
    d['onderweg'] += int(r['onderweg'] or 0)
    d['los_is_aanmaak'] += int(r['los_is_aanmaak'] or 0)
    if r['minuten'] is not None:
        d['min'].append(int(r['minuten']))


def q(v):
    return 'NULL' if v is None else str(v)


values = []
for m in sorted(per):
    d = per[m]
    mins = [x for x in d['min'] if x >= 0]
    mv = len(d['min'])
    b24 = sum(1 for x in mins if x <= 1440)
    bk = {
        'u0_4': sum(1 for x in mins if x <= 240),
        'u4_24': sum(1 for x in mins if 240 < x <= 1440),
        'u24_48': sum(1 for x in mins if 1440 < x <= 2880),
        'u48_168': sum(1 for x in mins if 2880 < x <= 10080),
        'u168_plus': sum(1 for x in mins if x > 10080),
    }
    med = round(statistics.median(mins) / 60, 1) if mins else None
    p90 = round(sorted(mins)[int(0.9 * (len(mins) - 1))] / 60, 1) if mins else None
    pct = round(100.0 * b24 / mv, 1) if mv else None
    pmv = round(100.0 * mv / d['inbounds'], 1) if d['inbounds'] else None
    neg = sum(1 for x in d['min'] if x < 0)
    values.append(
        f"(DATE '{m}-01', {d['inbounds']}, {mv}, {b24}, {q(pct)}, {q(pmv)}, {neg}, TIMESTAMPTZ '{nu}+00', "
        f"{q(med)}, {q(p90)}, {bk['u0_4']}, {bk['u4_24']}, {bk['u24_48']}, {bk['u48_168']}, {bk['u168_plus']}, "
        f"{d['inbounds'] - mv}, {d['onderweg']}, {d['los_is_aanmaak']})")
    st.write(f"D2S {m}: {pct}% binnen 24u, mediaan {med}u, dekking {pmv}%")

if not values:
    raise RuntimeError("D2S: geen rijen uit 7T, niets geschreven")

stmt = """
INSERT INTO kpi_data.dock_to_stock_maand (maand, inbounds, met_verplaatsing, binnen_24u, pct_binnen_24u, pct_met_verplaatsing, negatief, geschreven_op,
  mediaan_uren, p90_uren, u0_4, u4_24, u24_48, u48_168, u168_plus, zonder_verplaatsing, verplaatsing_onderweg, los_is_aanmaak)
VALUES """ + ",\n".join(values) + """
ON CONFLICT (maand) DO UPDATE SET
  inbounds = EXCLUDED.inbounds, met_verplaatsing = EXCLUDED.met_verplaatsing, binnen_24u = EXCLUDED.binnen_24u,
  pct_binnen_24u = EXCLUDED.pct_binnen_24u, pct_met_verplaatsing = EXCLUDED.pct_met_verplaatsing,
  negatief = EXCLUDED.negatief, geschreven_op = EXCLUDED.geschreven_op,
  mediaan_uren = EXCLUDED.mediaan_uren, p90_uren = EXCLUDED.p90_uren,
  u0_4 = EXCLUDED.u0_4, u4_24 = EXCLUDED.u4_24, u24_48 = EXCLUDED.u24_48, u48_168 = EXCLUDED.u48_168, u168_plus = EXCLUDED.u168_plus,
  zonder_verplaatsing = EXCLUDED.zonder_verplaatsing, verplaatsing_onderweg = EXCLUDED.verplaatsing_onderweg, los_is_aanmaak = EXCLUDED.los_is_aanmaak;
"""
schrijf(stmt, 'dock_to_stock_maand')
controleer('dock_to_stock_maand', len(values))

# ---------- 2. Schade en throughput (AWC operatie) ----------
schade = t7.fetch('DB7T', query=f"""
SELECT FORMAT(s.Los_Datum,'yyyy-MM') AS maand,
  COUNT(DISTINCT CASE WHEN m.Mutatiereden_ID = 35 THEN s.ID END) AS beschadigd_geleverd,
  COUNT(DISTINCT CASE WHEN m.Mutatiereden_ID = 34 THEN s.ID END) AS beschadigd_awc,
  COUNT(DISTINCT CASE WHEN m.Mutatiereden_ID = 33 THEN s.ID END) AS niet_geleverd,
  COUNT(DISTINCT CASE WHEN m.Mutatiereden_ID = 32 THEN s.ID END) AS artikelinfo_onjuist
FROM dbo.Spare_Orders s
JOIN dbo.Spare_Orderregels sr ON sr.Spare_Order_ID = s.ID
JOIN dbo.Spare_Orderregel_Mutaties m ON m.Spare_Orderregel_ID = sr.ID
WHERE s.Gelost = 1 AND s.Los_Datum >= '{VANAF}'
GROUP BY FORMAT(s.Los_Datum,'yyyy-MM')""")
# Outbound = fysieke uitleveringen: orders met een orderpicker, een pickscan of pallets.
# 7T maakt bij facturatie ook Logistieke_Orders aan (Status >= 90, geen picker, geen pickscan, 0 pallets,
# Aflever_Datum = factuurdatum). Die telden tot 2026-11-12 mee en maakten outbound ~2,5x te hoog.
uit = t7.fetch('DB7T', query=f"""
SELECT FORMAT(lo.Aflever_Datum,'yyyy-MM') AS maand,
  SUM(CASE WHEN lo.Orderpicker_Gebr_ID IS NOT NULL OR lo.Aantal_Pallets > 0 OR ps.LogOrder_ID IS NOT NULL
           THEN 1 ELSE 0 END) AS outbound_orders,
  COUNT(*) AS alle_log_orders
FROM dbo.Logistieke_Orders lo
LEFT JOIN (
  SELECT DISTINCT LogOrder_ID FROM dbo.Logorder_Pickstatus
  WHERE Datum >= DATEADD(DAY, -60, CAST('{VANAF}' AS date))
) ps ON ps.LogOrder_ID = lo.ID
WHERE lo.Statussoort = 'Log' AND lo.Status >= 90 AND lo.Aflever_Datum >= '{VANAF}'
GROUP BY FORMAT(lo.Aflever_Datum,'yyyy-MM')""")
# Throughput sinds 2026-11-13 (Mark): zendingen in 7T (dbo.Zendingen) per maand van de laaddatum,
# met minstens één order en een laaddatum die niet in de toekomst ligt. De status zegt niets over
# vertrek (86% blijft op 10 'in bewerking'), dus alle statussen tellen mee.
zend = t7.fetch('DB7T', query=f"""
SELECT FORMAT(z.Laaddatum,'yyyy-MM') AS maand, COUNT(*) AS zendingen
FROM dbo.Zendingen z
WHERE z.Statussoort = 'ZEND' AND z.Laaddatum >= '{VANAF}' AND z.Laaddatum <= GETDATE()
  AND ISNULL(z.Aantal_Orders, 0) > 0
GROUP BY FORMAT(z.Laaddatum,'yyyy-MM')""")
if not zend:
    raise RuntimeError("zendingen: geen rijen uit 7T, niets geschreven")
zd = {str(r['maand'])[:7]: int(r['zendingen'] or 0) for r in zend}
sd = {str(r['maand'])[:7]: r for r in schade}
ud = {str(r['maand'])[:7]: r for r in uit}
alle = sorted(set(per) | set(ud) | set(zd))
vals2 = []
for m in alle:
    p = per.get(m, {'inbounds': 0, 'min': []})
    s_ = sd.get(m, {})
    vals2.append(f"(DATE '{m}-01', {p['inbounds']}, {len(p['min'])}, {int(ud.get(m, {}).get('outbound_orders', 0) or 0)}, "
                 f"{int(s_.get('beschadigd_geleverd', 0) or 0)}, {int(s_.get('beschadigd_awc', 0) or 0)}, "
                 f"{int(s_.get('niet_geleverd', 0) or 0)}, {int(s_.get('artikelinfo_onjuist', 0) or 0)}, TIMESTAMPTZ '{nu}+00', {zd.get(m, 0)})")
    st.write(f"OPS {m}: inbound {p['inbounds']}, zendingen {zd.get(m, 0)}, outbound {ud.get(m, {}).get('outbound_orders', 0)} (van {ud.get(m, {}).get('alle_log_orders', 0)} log-orders incl. factuurorders), schade {s_.get('beschadigd_geleverd', 0)}/{s_.get('beschadigd_awc', 0)}")
schrijf("""
CREATE TABLE IF NOT EXISTS kpi_data.awc_operatie_maand (
  maand date PRIMARY KEY, inbounds integer, inbounds_met_verplaatsing integer, outbound_orders integer,
  beschadigd_geleverd integer, beschadigd_awc integer, niet_geleverd integer, artikelinfo_onjuist integer,
  geschreven_op timestamptz);
ALTER TABLE kpi_data.awc_operatie_maand ADD COLUMN IF NOT EXISTS outbound_zendingen integer;
INSERT INTO kpi_data.awc_operatie_maand (maand, inbounds, inbounds_met_verplaatsing, outbound_orders,
  beschadigd_geleverd, beschadigd_awc, niet_geleverd, artikelinfo_onjuist, geschreven_op, outbound_zendingen)
VALUES """ + ",\n".join(vals2) + """
ON CONFLICT (maand) DO UPDATE SET inbounds = EXCLUDED.inbounds, inbounds_met_verplaatsing = EXCLUDED.inbounds_met_verplaatsing,
  outbound_orders = EXCLUDED.outbound_orders, beschadigd_geleverd = EXCLUDED.beschadigd_geleverd, beschadigd_awc = EXCLUDED.beschadigd_awc,
  niet_geleverd = EXCLUDED.niet_geleverd, artikelinfo_onjuist = EXCLUDED.artikelinfo_onjuist, geschreven_op = EXCLUDED.geschreven_op,
  outbound_zendingen = EXCLUDED.outbound_zendingen;
""", 'awc_operatie_maand')
controleer('awc_operatie_maand', len(vals2))

# ---------- 3. Schade per klant (awc_schade_klant_maand) ----------
# Zelfde basis als awc_operatie_maand: geloste inbounds (Gelost=1) per Los_Datum-maand, per eigenaar-relatie;
# beschadigd_geleverd = inbounds met minstens een orderregel-mutatie reden 35. Per maand tellen de klanten op
# tot beschadigd_geleverd / inbounds in awc_operatie_maand.
klant_rows = t7.fetch('DB7T', query=f"""
SELECT FORMAT(s.Los_Datum,'yyyy-MM') AS maand, COALESCE(s.Eigenaar_Relatie_ID, 0) AS relatie_id,
  MAX(r.Zoeknaam) AS klant,
  COUNT(DISTINCT s.ID) AS inbounds,
  COUNT(DISTINCT CASE WHEN d.so IS NOT NULL THEN s.ID END) AS beschadigd_geleverd
FROM dbo.Spare_Orders s
LEFT JOIN dbo.Relaties r ON r.ID = s.Eigenaar_Relatie_ID
LEFT JOIN (
  SELECT DISTINCT sr.Spare_Order_ID AS so
  FROM dbo.Spare_Orderregels sr JOIN dbo.Spare_Orderregel_Mutaties m ON m.Spare_Orderregel_ID = sr.ID
  WHERE m.Mutatiereden_ID = 35
) d ON d.so = s.ID
WHERE s.Gelost = 1 AND s.Los_Datum >= '{VANAF}'
GROUP BY FORMAT(s.Los_Datum,'yyyy-MM'), COALESCE(s.Eigenaar_Relatie_ID, 0)""")


def sq(v):
    return 'NULL' if v is None else "'" + str(v).replace("'", "''") + "'"


vals3 = []
tot3 = {}
for r in klant_rows:
    m = str(r['maand'])[:7]
    inb = int(r['inbounds'] or 0)
    sch = int(r['beschadigd_geleverd'] or 0)
    t = tot3.setdefault(m, [0, 0])
    t[0] += inb
    t[1] += sch
    klant = r['klant'] if r['klant'] is not None else '(onbekend)'
    vals3.append(f"(DATE '{m}-01', {int(r['relatie_id'])}, {sq(klant)}, {inb}, {sch}, TIMESTAMPTZ '{nu}+00')")
for m in sorted(tot3):
    p = per.get(m, {'inbounds': 0})
    s_ = int(sd.get(m, {}).get('beschadigd_geleverd', 0) or 0)
    st.write(f"KLANT {m}: inbounds {tot3[m][0]} (ops {p['inbounds']}), schade {tot3[m][1]} (ops {s_})")
if not vals3:
    raise RuntimeError("schade per klant: geen rijen uit 7T, niets geschreven")
schrijf("""
INSERT INTO kpi_data.awc_schade_klant_maand (maand, relatie_id, klant, inbounds, beschadigd_geleverd, geschreven_op)
VALUES """ + ",\n".join(vals3) + """
ON CONFLICT (maand, relatie_id) DO UPDATE SET klant = EXCLUDED.klant, inbounds = EXCLUDED.inbounds,
  beschadigd_geleverd = EXCLUDED.beschadigd_geleverd, geschreven_op = EXCLUDED.geschreven_op;
""", 'awc_schade_klant_maand')
controleer('awc_schade_klant_maand', len(vals3))

try:
    pq.refresh_database(database_name=DW, is_async=False)
except Exception as e:
    st.write(f"refresh: {e}")
c1 = dw.fetch(DW, query="SELECT COUNT(*) AS n, MAX(geschreven_op) AS laatst FROM kpi_data.dock_to_stock_maand")
c2 = dw.fetch(DW, query="SELECT COUNT(*) AS n, MAX(geschreven_op) AS laatst FROM kpi_data.awc_operatie_maand")
c3 = dw.fetch(DW, query="SELECT COUNT(*) AS n, SUM(beschadigd_geleverd) AS schade, MAX(geschreven_op) AS laatst FROM kpi_data.awc_schade_klant_maand")
st.write(f"Klaar. dock_to_stock_maand: {c1} | awc_operatie_maand: {c2} | awc_schade_klant_maand: {c3}")
