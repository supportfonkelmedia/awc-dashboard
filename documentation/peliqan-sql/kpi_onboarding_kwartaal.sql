-- Peliqan "My Queries".kpi_onboarding_kwartaal (table_id 1416429), stand 2026-11-12
WITH t AS (
  SELECT createdate AS start_ts,
         COALESCE(CAST(NULLIF(hs_date_entered_248014792,'') AS timestamptz), closed_date) AS eind_ts
  FROM hubspot_v2.tickets
  WHERE TRIM(hs_pipeline) = '121633735' AND COALESCE(archived,false) = false
    AND TRIM(hs_pipeline_stage) = '248014792'
)
SELECT DATE_TRUNC('quarter', eind_ts)::date AS kwartaal,
  'AWC' AS pijplijn,
  COUNT(*) AS afgerond,
  ROUND(CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (eind_ts - start_ts))/86400) AS numeric), 1) AS mediaan_dagen,
  (DATE_TRUNC('quarter', eind_ts)::date = DATE_TRUNC('quarter', CURRENT_DATE)::date) AS lopend_kwartaal
FROM t
WHERE eind_ts IS NOT NULL AND eind_ts >= start_ts AND eind_ts >= '2024-01-01' AND eind_ts <= NOW()
GROUP BY 1
