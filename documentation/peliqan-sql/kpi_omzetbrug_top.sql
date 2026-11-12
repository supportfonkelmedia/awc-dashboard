-- Peliqan "My Queries".kpi_omzetbrug_top (table_id 1416723), stand 2026-11-12
SELECT scope, CASE WHEN rang_groei <= 10 THEN 'groei' ELSE 'krimp' END AS lijst,
  CASE WHEN rang_groei <= 10 THEN rang_groei ELSE rang_krimp END AS rang,
  naam, entiteiten, omzet_vorig, omzet_nu, verschil, component, stand_per
FROM "My Queries".kpi_omzetbrug_klant
WHERE rang_groei <= 10 OR rang_krimp <= 10
ORDER BY CASE scope WHEN 'Concern' THEN 0 WHEN 'AWC' THEN 1 WHEN 'AFC' THEN 2 ELSE 3 END, lijst, rang
