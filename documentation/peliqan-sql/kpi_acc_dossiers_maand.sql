-- Peliqan "My Queries".kpi_acc_dossiers_maand (table_id 1416427), stand 2026-11-12
WITH t AS (
  SELECT
    CAST(DATE_TRUNC('MONTH', createdate) AS DATE) AS maand,
    CASE TRIM(COALESCE(type_aanvraag, ''))
      WHEN 'Import'
      THEN 'Import'
      WHEN 'Export'
      THEN 'Export'
      WHEN 'Consult'
      THEN 'Consult'
      ELSE 'Overig'
    END AS soort
  FROM hubspot_v2.tickets
  WHERE
    TRIM(hs_pipeline) = '1283749104'
    AND COALESCE(archived, FALSE) = FALSE
    AND createdate >= '2025-01-01'
    AND createdate <= CURRENT_TIMESTAMP
)
SELECT
  maand,
  soort,
  COUNT(*) AS dossiers,
  (
    maand = CAST(DATE_TRUNC('MONTH', CURRENT_DATE) AS DATE)
  ) AS lopende_maand
FROM t
GROUP BY
  maand,
  soort
