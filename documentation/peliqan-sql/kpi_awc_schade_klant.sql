-- Peliqan "My Queries".kpi_awc_schade_klant (table_id 1419084), stand 2026-11-12
WITH jaar AS (
  SELECT relatie_id, MAX(klant) AS klant, SUM(inbounds) AS inbounds, SUM(beschadigd_geleverd) AS beschadigd
  FROM kpi_data.awc_schade_klant_maand
  WHERE maand >= CAST(DATE_TRUNC('year', CURRENT_DATE) AS date)
  GROUP BY relatie_id
),
tot AS (SELECT SUM(beschadigd) AS alle_schade, SUM(inbounds) AS alle_inbounds FROM jaar)
SELECT j.relatie_id, j.klant, j.inbounds, j.beschadigd,
  ROUND(100.0 * j.beschadigd / NULLIF(j.inbounds, 0), 1) AS pct_beschadigd,
  ROUND(100.0 * j.beschadigd / NULLIF(t.alle_schade, 0), 1) AS aandeel_in_schade,
  ROUND(100.0 * j.inbounds / NULLIF(t.alle_inbounds, 0), 1) AS aandeel_in_inbounds,
  RANK() OVER (ORDER BY j.beschadigd DESC, j.inbounds DESC) AS rang
FROM jaar j CROSS JOIN tot t
WHERE j.beschadigd > 0
