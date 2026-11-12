-- Peliqan "My Queries".kpi_afc_sprinter_tegel (table_id 1578025), stand 2026-11-12 vóór de AFC-tegelwijziging
WITH m AS (
  SELECT * FROM "My Queries".kpi_afc_sprinter_maand WHERE status = 'volledig'
), l AS (
  SELECT * FROM m ORDER BY maand DESC LIMIT 1
), p AS (
  SELECT m.* FROM m JOIN l ON m.maand = CAST(l.maand - INTERVAL '1 month' AS date)
), k AS (
  SELECT 'afc_zendingen' AS kpi_code, CAST(l.zendingen AS numeric) AS waarde, CAST(p.zendingen AS numeric) AS waarde_vorige, l.* FROM l LEFT JOIN p ON true
  UNION ALL
  SELECT 'afc_modal_split', l.pct_weg, p.pct_weg, l.* FROM l LEFT JOIN p ON true
  UNION ALL
  SELECT 'afc_marge_per_zending', l.marge_per_zending, p.marge_per_zending, l.* FROM l LEFT JOIN p ON true
)
SELECT kpi_code,
  'pgl1' AS scope_code,
  'AFC' AS scope_label,
  waarde,
  waarde_vorige,
  waarde - waarde_vorige AS delta,
  CAST(zendingen AS bigint) AS n,
  CAST(NULL AS text) AS leeg_reden,
  'Zendingen met rapportdatum in ' || TO_CHAR(maand, 'MM-YYYY') || ', zonder geannuleerde' AS venster,
  maand AS stand_per,
  (SELECT MAX(_sdc_batched_at) FROM sprinter_api.shipments) AS bron_bijgewerkt,
  zendingen || ' zendingen: ' || weg || ' weg, ' || zee || ' zee, ' || lucht || ' lucht. Marge totaal ' || ROUND(marge_totaal) || ' euro.' AS toelichting
FROM k
