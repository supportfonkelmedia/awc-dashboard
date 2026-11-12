-- Peliqan "My Queries".kpi_churn_kwartaal (table_id 1416430), stand 2026-11-12
WITH c AS (
  SELECT
    CAST(NULLIF(hs_v2_date_exited_customer, '') AS TIMESTAMPTZ) AS vertrek_ts,
    (
      CASE WHEN icp__euhubbehoefte = 'Yes' THEN 1 ELSE 0 END + CASE WHEN icp__meerjarige_samenwerking = 'Yes' THEN 1 ELSE 0 END + CASE WHEN icp__noneu_naar_eu_stromen = 'Yes' THEN 1 ELSE 0 END + CASE WHEN icp__premium__compliance_mindset = 'Yes' THEN 1 ELSE 0 END + CASE WHEN icp__producent__brand_owner = 'Yes' THEN 1 ELSE 0 END
    ) AS icp_ja,
    (
      NOT NULLIF(icp__euhubbehoefte, '') IS NULL
      OR NOT NULLIF(icp__meerjarige_samenwerking, '') IS NULL
      OR NOT NULLIF(icp__noneu_naar_eu_stromen, '') IS NULL
      OR NOT NULLIF(icp__premium__compliance_mindset, '') IS NULL
      OR NOT NULLIF(icp__producent__brand_owner, '') IS NULL
    ) AS gescoord
  FROM hubspot_v2.companies
  WHERE
    COALESCE(archived, FALSE) = FALSE
    AND NOT NULLIF(hs_v2_date_exited_customer, '') IS NULL
), d AS (
  SELECT
    c.*,
    COUNT(*) OVER (PARTITION BY DATE(vertrek_ts)) AS per_dag
  FROM c
), k AS (
  SELECT
    CAST(GENERATE_SERIES(
      CAST('2024-01-01' AS DATE),
      CAST(DATE_TRUNC('QUARTER', CURRENT_DATE) AS DATE),
      INTERVAL '3 MONTHS'
    ) AS DATE) AS kwartaal
)
SELECT
  k.kwartaal,
  'Q' || EXTRACT(QUARTER FROM k.kwartaal) || ' ' || EXTRACT(YEAR FROM k.kwartaal) AS label,
  COUNT(d.vertrek_ts) AS vertrokken,
  COUNT(d.vertrek_ts) FILTER(WHERE
    d.per_dag >= 10) AS waarvan_bulk,
  COUNT(d.vertrek_ts) FILTER(WHERE
    d.gescoord) AS gescoord,
  COUNT(d.vertrek_ts) FILTER(WHERE
    d.gescoord AND d.icp_ja >= 4) AS icp_vertrokken,
  (
    k.kwartaal = CAST(DATE_TRUNC('QUARTER', CURRENT_DATE) AS DATE)
  ) AS lopend_kwartaal
FROM k
LEFT JOIN d
  ON CAST(DATE_TRUNC('QUARTER', d.vertrek_ts) AS DATE) = k.kwartaal
  AND d.vertrek_ts <= CURRENT_TIMESTAMP
GROUP BY
  k.kwartaal
