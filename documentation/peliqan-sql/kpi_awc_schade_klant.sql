-- Peliqan "My Queries".kpi_awc_schade_klant (table_id 1419084), stand 2026-11-12 na jaarwisselingsfix: in januari het hele vorige jaar (CTE p) in plaats van alleen de lopende januari. Vorige versie: commit 66cd6a6.
WITH p AS (
  SELECT CAST(DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 month') AS date) AS van,
    CAST(DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 month') + INTERVAL '1 year' AS date) AS tot
),
jaar AS (
  SELECT s.relatie_id, MAX(s.klant) AS klant, SUM(s.inbounds) AS inbounds, SUM(s.beschadigd_geleverd) AS beschadigd
  FROM kpi_data.awc_schade_klant_maand AS s, p
  WHERE s.maand >= p.van AND s.maand < p.tot
  GROUP BY s.relatie_id
),
tot AS (SELECT SUM(beschadigd) AS alle_schade, SUM(inbounds) AS alle_inbounds FROM jaar)
SELECT j.relatie_id, j.klant, j.inbounds, j.beschadigd,
  ROUND(100.0 * j.beschadigd / NULLIF(j.inbounds, 0), 1) AS pct_beschadigd,
  ROUND(100.0 * j.beschadigd / NULLIF(t.alle_schade, 0), 1) AS aandeel_in_schade,
  ROUND(100.0 * j.inbounds / NULLIF(t.alle_inbounds, 0), 1) AS aandeel_in_inbounds,
  RANK() OVER (ORDER BY j.beschadigd DESC, j.inbounds DESC) AS rang
FROM jaar j CROSS JOIN tot t
WHERE j.beschadigd > 0
