-- Peliqan "My Queries".kpi_awc_ops_maand (table_id 1419015), stand 2026-11-12
SELECT maand, inbounds, inbounds_met_verplaatsing, outbound_orders,
  beschadigd_geleverd, beschadigd_awc, niet_geleverd, artikelinfo_onjuist,
  ROUND(100.0 * beschadigd_geleverd / NULLIF(inbounds, 0), 1) AS pct_beschadigd_geleverd,
  ROUND(100.0 * beschadigd_awc / NULLIF(inbounds, 0), 2) AS pct_beschadigd_awc,
  ROUND(100.0 * (beschadigd_geleverd + niet_geleverd + artikelinfo_onjuist + beschadigd_awc) / NULLIF(inbounds, 0), 1) AS pct_met_manco,
  (maand < CAST(DATE_TRUNC('month', CURRENT_DATE) AS date)) AS afgesloten,
  CASE WHEN maand >= CAST(DATE_TRUNC('month', CURRENT_DATE) AS date) THEN 'voorlopig' ELSE 'definitief' END AS status,
  geschreven_op
FROM kpi_data.awc_operatie_maand
