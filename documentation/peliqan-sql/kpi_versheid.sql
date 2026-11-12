-- Peliqan "My Queries".kpi_versheid (table_id 1416384), stand 2026-11-12
WITH bronnen AS (
  SELECT 'Cashweb' AS bron, MAX(_sdc_batched_at) AS laatst_bijgewerkt, 36 AS max_uren
  FROM cashweb.ledger_mutations WHERE admin_code IN ('alaw','pgl1','acco')
  UNION ALL
  SELECT 'HubSpot', MAX(_sdc_batched_at), 36 FROM hubspot_v2.deals
  UNION ALL
  SELECT 'Sprinter3000', MAX(_sdc_batched_at), 36 FROM sprinter3000.shipments
  UNION ALL
  SELECT '7T', CAST(NULL AS timestamptz), 36
),
b AS (
  SELECT bron, laatst_bijgewerkt, max_uren,
    ROUND(CAST(EXTRACT(EPOCH FROM (NOW() - laatst_bijgewerkt)) / 3600 AS numeric), 1) AS uren_oud,
    CASE
      WHEN bron = '7T' THEN 'onbekend: 7T staat niet in de warehouse'
      WHEN laatst_bijgewerkt IS NULL THEN 'geen data'
      WHEN NOW() - laatst_bijgewerkt > max_uren * INTERVAL '1 hour' THEN 'verouderd'
      ELSE 'actueel'
    END AS status
  FROM bronnen
)
SELECT b.*,
  (SELECT bron FROM b b2 WHERE b2.laatst_bijgewerkt IS NOT NULL ORDER BY b2.laatst_bijgewerkt ASC LIMIT 1) AS oudste_bron,
  (SELECT MIN(laatst_bijgewerkt) FROM b) AS oudste_bijgewerkt
FROM b
