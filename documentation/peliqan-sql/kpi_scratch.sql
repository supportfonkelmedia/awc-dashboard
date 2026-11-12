-- Peliqan "My Queries".kpi_scratch (table_id 1416426), stand 2026-11-12
SELECT
  scope,
  naam,
  klant,
  omzet_vorig,
  omzet_nu
FROM "My Queries".kpi_omzetbrug_klant
WHERE
  naam ILIKE '%amsterdam%'
  OR naam ILIKE '%AWC%'
  OR naam ILIKE '%AFC%'
  OR naam ILIKE '%ACC %'
  OR klant ILIKE '%AMSTERDAM%'
ORDER BY
  scope,
  omzet_nu DESC
