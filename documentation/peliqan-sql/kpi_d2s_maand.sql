-- Peliqan "My Queries".kpi_d2s_maand (table_id 1416856), stand 2026-11-12
SELECT
  maand,
  inbounds,
  met_verplaatsing,
  zonder_verplaatsing,
  pct_met_verplaatsing AS dekking_pct,
  binnen_24u,
  pct_binnen_24u,
  mediaan_uren,
  p90_uren,
  u0_4 AS binnen_4u,
  u4_24 AS tussen_4_24u,
  u24_48 AS tussen_1_2_dagen,
  u48_168 AS tussen_2_7_dagen,
  u168_plus AS langer_dan_week,
  verplaatsing_onderweg,
  los_is_aanmaak,
  (
    maand < CAST(DATE_TRUNC('MONTH', CURRENT_DATE) AS DATE)
  ) AS afgesloten,
  CASE
    WHEN maand >= CAST(DATE_TRUNC('MONTH', CURRENT_DATE) AS DATE)
    THEN 'voorlopig'
    ELSE 'definitief'
  END AS status,
  geschreven_op
FROM kpi_data.dock_to_stock_maand
