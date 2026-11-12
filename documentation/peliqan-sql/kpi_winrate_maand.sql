-- Peliqan "My Queries".kpi_winrate_maand (table_id 1416341), stand 2026-11-12
WITH peil AS (
  SELECT CAST(g AS date) AS peildatum, 'maandeinde' AS soort
  FROM GENERATE_SERIES(DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '12 months', DATE_TRUNC('month', CURRENT_DATE), INTERVAL '1 month') g
  UNION ALL SELECT CURRENT_DATE, 'vandaag'
  UNION ALL SELECT CAST(CURRENT_DATE - INTERVAL '1 month' AS date), 'vandaag_min_1_maand'
),
pl AS (SELECT DISTINCT pipeline FROM "My Queries".kpi_winrate_basis)
SELECT pl.pipeline, pe.peildatum, pe.soort,
  COUNT(b.deal_id) AS aangemaakt,
  COUNT(b.deal_id) FILTER (WHERE b.uitkomst = 'gewonnen' AND b.beslisdatum < pe.peildatum) AS gewonnen,
  COUNT(b.deal_id) FILTER (WHERE b.uitkomst = 'verloren' AND b.beslisdatum < pe.peildatum) AS verloren,
  COUNT(b.deal_id) FILTER (WHERE b.hubspot_vlag_gewonnen AND b.beslisdatum < pe.peildatum) AS gewonnen_alleen_hubspot_vlag
FROM pl CROSS JOIN peil pe
LEFT JOIN "My Queries".kpi_winrate_basis b
  ON b.pipeline = pl.pipeline
 AND b.createdate >= pe.peildatum - INTERVAL '12 months'
 AND b.createdate < pe.peildatum
GROUP BY pl.pipeline, pe.peildatum, pe.soort
