-- Peliqan "My Queries".kpi_afc_sprinter_tegel (table_id 1578025), live stand 2026-11-12 na AFC Quote conversion (vorige stand: git-historie)
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
UNION ALL
SELECT 'afc_quote_conversie' AS kpi_code,
  'pgl1' AS scope_code,
  'AFC' AS scope_label,
  ol.conversie_pct AS waarde,
  op.conversie_pct AS waarde_vorige,
  ol.conversie_pct - op.conversie_pct AS delta,
  CAST(ol.beslist AS bigint) AS n,
  CAST(NULL AS text) AS leeg_reden,
  'Offertes aangemaakt van ' || TO_CHAR(ol.maand - INTERVAL '11 month', 'MM-YYYY') || ' t/m ' || TO_CHAR(ol.maand, 'MM-YYYY') || ', met een uitkomst' AS venster,
  ol.maand AS stand_per,
  (SELECT MAX(_sdc_batched_at) FROM sprinter_api.quotations) AS bron_bijgewerkt,
  ol.gewonnen || ' gewonnen, ' || ol.afgewezen || ' afgewezen, ' || ol.verlopen || ' verlopen. ' || ol.nog_open || ' offertes staan nog open en tellen niet mee.' AS toelichting
FROM "My Queries".kpi_afc_offerte_maand_my_queries AS ol
LEFT JOIN "My Queries".kpi_afc_offerte_maand_my_queries AS op ON op.maand = CAST(ol.maand - INTERVAL '1 month' AS date)
WHERE ol.maand = CAST(DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' AS date)
