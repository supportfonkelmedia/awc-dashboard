-- Peliqan "My Queries".kpi_acc_doorlooptijd_maand (table_id 1416428), stand 2026-11-12
WITH t AS (
  SELECT
    createdate AS start_ts,
    COALESCE(closed_date, CAST(NULLIF(hs_date_entered_1754175726, '') AS TIMESTAMPTZ)) AS eind_ts
  FROM hubspot_v2.tickets
  WHERE
    TRIM(hs_pipeline) = '1283749104'
    AND COALESCE(archived, FALSE) = FALSE
    AND TRIM(hs_pipeline_stage) = '1754175726'
)
SELECT
  CAST(DATE_TRUNC('MONTH', eind_ts) AS DATE) AS maand,
  COUNT(*) AS afgerond,
  ROUND(
    CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
      EXTRACT(EPOCH FROM (
        eind_ts - start_ts
      )) / 86400) AS DECIMAL),
    1
  ) AS mediaan_dagen,
  ROUND(CAST(AVG(EXTRACT(EPOCH FROM (
    eind_ts - start_ts
  )) / 86400) AS DECIMAL), 1) AS gemiddeld_dagen,
  (
    CAST(DATE_TRUNC('MONTH', eind_ts) AS DATE) = CAST(DATE_TRUNC('MONTH', CURRENT_DATE) AS DATE)
  ) AS lopende_maand
FROM t
WHERE
  NOT eind_ts IS NULL
  AND eind_ts >= start_ts
  AND eind_ts >= '2025-03-01'
  AND eind_ts <= CURRENT_TIMESTAMP
GROUP BY
  1
