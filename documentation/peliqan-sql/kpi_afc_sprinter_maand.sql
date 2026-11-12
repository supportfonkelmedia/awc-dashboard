-- Peliqan "My Queries".kpi_afc_sprinter_maand (table_id 1419142), stand 2026-11-12
WITH m AS (
  SELECT CAST(DATE_TRUNC('month', report_date) AS date) AS maand,
    COUNT(*) AS zendingen,
    SUM(CASE WHEN shipment_mode = 'R' THEN 1 ELSE 0 END) AS weg,
    SUM(CASE WHEN shipment_mode = 'S' THEN 1 ELSE 0 END) AS zee,
    SUM(CASE WHEN shipment_mode = 'A' THEN 1 ELSE 0 END) AS lucht,
    SUM(CASE WHEN shipment_mode NOT IN ('R','S','A') OR shipment_mode IS NULL THEN 1 ELSE 0 END) AS overig,
    ROUND(CAST(SUM(COALESCE(total_gpm_amount, 0)) AS numeric), 2) AS marge_totaal,
    ROUND(CAST(AVG(CASE WHEN shipment_mode = 'R' THEN total_gpm_amount END) AS numeric), 2) AS marge_gem_weg,
    ROUND(CAST(AVG(CASE WHEN shipment_mode = 'S' THEN total_gpm_amount END) AS numeric), 2) AS marge_gem_zee,
    ROUND(CAST(AVG(CASE WHEN shipment_mode = 'A' THEN total_gpm_amount END) AS numeric), 2) AS marge_gem_lucht,
    MAX(_sdc_batched_at) AS laatst_gesynct
  FROM sprinter_api.shipments
  WHERE report_date >= '2024-12-01'
    AND COALESCE(shipment_status_code, '') <> 'C'
  GROUP BY 1
)
SELECT maand, zendingen, weg, zee, lucht, overig,
  ROUND(100.0 * weg / NULLIF(zendingen, 0), 1) AS pct_weg,
  ROUND(100.0 * zee / NULLIF(zendingen, 0), 1) AS pct_zee,
  ROUND(100.0 * lucht / NULLIF(zendingen, 0), 1) AS pct_lucht,
  marge_totaal,
  ROUND(marge_totaal / NULLIF(zendingen, 0), 2) AS marge_per_zending,
  marge_gem_weg, marge_gem_zee, marge_gem_lucht,
  CASE
    WHEN maand >= CAST(DATE_TRUNC('month', CURRENT_DATE) AS date) THEN 'voorlopig'
    ELSE 'volledig'
  END AS status,
  laatst_gesynct
FROM m
