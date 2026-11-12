-- Peliqan "My Queries".kpi_winrate_tegel (table_id 1416342), stand 2026-11-12
WITH p AS (
  SELECT pipeline,
    MAX(CASE WHEN soort='vandaag' THEN gewonnen END) AS w,
    MAX(CASE WHEN soort='vandaag' THEN verloren END) AS l,
    MAX(CASE WHEN soort='vandaag' THEN aangemaakt END) AS aangemaakt,
    MAX(CASE WHEN soort='vandaag' THEN gewonnen_alleen_hubspot_vlag END) AS w_vlag,
    MAX(CASE WHEN soort='vandaag_min_1_maand' THEN gewonnen END) AS w_v,
    MAX(CASE WHEN soort='vandaag_min_1_maand' THEN verloren END) AS l_v
  FROM "My Queries".kpi_winrate_maand GROUP BY pipeline
),
beslist_12m AS (
  SELECT pipeline,
    COUNT(*) FILTER (WHERE uitkomst='gewonnen') AS w,
    COUNT(*) FILTER (WHERE uitkomst='verloren') AS l
  FROM "My Queries".kpi_winrate_basis
  WHERE beslisdatum >= CURRENT_DATE - INTERVAL '12 months'
  GROUP BY pipeline
),
fr AS (SELECT MAX(_sdc_batched_at) AS bijgewerkt FROM "My Queries".kpi_winrate_basis),
minimum AS (SELECT 20 AS min_n)
SELECT
  'winrate' AS kpi_code,
  p.pipeline AS scope_code,
  p.pipeline AS scope_label,
  CASE WHEN p.w + p.l >= m.min_n THEN ROUND(100.0 * p.w / (p.w + p.l), 1) END AS waarde,
  CASE WHEN p.w_v + p.l_v >= m.min_n THEN ROUND(100.0 * p.w_v / (p.w_v + p.l_v), 1) END AS waarde_vorige_maand,
  CASE WHEN p.w + p.l >= m.min_n AND p.w_v + p.l_v >= m.min_n
       THEN ROUND(100.0 * p.w / (p.w + p.l) - 100.0 * p.w_v / (p.w_v + p.l_v), 1) END AS delta_procentpunt,
  p.w AS gewonnen, p.l AS verloren, p.w + p.l AS n_beslist, p.aangemaakt - p.w - p.l AS nog_open, m.min_n,
  CASE WHEN p.w + p.l < m.min_n THEN 'Te weinig afgesloten deals: ' || (p.w + p.l) || ' van minimaal ' || m.min_n END AS leeg_reden,
  CASE WHEN p.w + p.l >= m.min_n THEN ROUND(100.0 * p.w_vlag / (p.w + p.l), 1) END AS waarde_alleen_hubspot_vlag,
  CASE WHEN b.w + b.l >= m.min_n THEN ROUND(100.0 * b.w / (b.w + b.l), 1) END AS waarde_op_beslisdatum,
  'Deals aangemaakt in de laatste 12 maanden met een uitkomst' AS venster,
  CURRENT_DATE AS stand_per,
  fr.bijgewerkt AS bron_bijgewerkt,
  CAST(NULL AS numeric) AS doel,
  CAST(NULL AS text) AS status,
  'geen doel ingesteld' AS doel_tekst,
  'Andere lezing: op deals die in de laatste 12 maanden zijn beslist (ongeacht aanmaakdatum) is de winrate '
    || COALESCE(CAST(CASE WHEN b.w + b.l >= m.min_n THEN ROUND(100.0 * b.w / (b.w + b.l), 1) END AS text) || '%', 'niet te berekenen') || '.' AS toelichting
FROM p CROSS JOIN minimum m CROSS JOIN fr
LEFT JOIN beslist_12m b ON b.pipeline = p.pipeline
