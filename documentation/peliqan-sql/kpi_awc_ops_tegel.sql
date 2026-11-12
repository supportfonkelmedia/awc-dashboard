-- Peliqan "My Queries".kpi_awc_ops_tegel (table_id 1419016), stand 2026-11-12
WITH e AS (SELECT CAST(DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' AS date) AS m),
nu AS (SELECT o.* FROM "My Queries".kpi_awc_ops_maand o CROSS JOIN e WHERE o.maand = e.m),
vg AS (SELECT o.* FROM "My Queries".kpi_awc_ops_maand o CROSS JOIN e WHERE o.maand = CAST(e.m - INTERVAL '1 month' AS date))
SELECT 'damage_rate' AS kpi_code, 'alaw' AS scope_code, 'AWC' AS scope_label,
  nu.pct_beschadigd_geleverd AS waarde, vg.pct_beschadigd_geleverd AS waarde_vorige,
  nu.pct_beschadigd_geleverd - vg.pct_beschadigd_geleverd AS delta,
  CAST(nu.inbounds AS bigint) AS n, CAST(NULL AS text) AS leeg_reden,
  'Inbounds gelost in ' || TO_CHAR(nu.maand, 'MM-YYYY') AS venster, nu.maand AS stand_per, nu.geschreven_op AS bron_bijgewerkt,
  nu.beschadigd_geleverd || ' van ' || nu.inbounds || ' inbounds beschadigd aangeleverd; ' || nu.beschadigd_awc || ' beschadigd door AWC; ' || nu.niet_geleverd || ' niet geleverd.' AS toelichting
FROM nu CROSS JOIN vg
UNION ALL
SELECT 'throughput', 'alaw', 'AWC',
  CAST(nu.outbound_orders AS numeric), CAST(vg.outbound_orders AS numeric), CAST(nu.outbound_orders - vg.outbound_orders AS numeric),
  CAST(nu.outbound_orders AS bigint), CAST(NULL AS text),
  'Afgeronde uitleveringen in ' || TO_CHAR(nu.maand, 'MM-YYYY'), nu.maand, nu.geschreven_op,
  'Uitgaand ' || nu.outbound_orders || ' orders; inkomend ' || nu.inbounds || ' geloste inbounds, waarvan ' || nu.inbounds_met_verplaatsing || ' met een verplaatsing.'
FROM nu CROSS JOIN vg
