-- Peliqan "My Queries".kpi_triple_lob_te_controleren (table_id 1416459), stand 2026-11-12
WITH r AS (
  SELECT admin_code, TRIM(relation_number) AS relation_number,
    MIN(UPPER(REGEXP_REPLACE(TRIM(search_name), '[^A-Za-z0-9]', '', 'g'))) AS zoek,
    MIN(TRIM(name)) AS naam, MIN(TRIM(postal_code)) AS postcode, MIN(TRIM(country_code)) AS land
  FROM cashweb.relation WHERE admin_code IN ('alaw','pgl1','acco') GROUP BY 1,2
),
e AS (SELECT CAST(DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months' AS date) AS eind),
km AS (
  SELECT k.admin_code, r.zoek, r.naam, r.postcode, r.land, k.omzet
  FROM "My Queries".kpi_klant_omzet_maand k
  JOIN r ON r.admin_code = k.admin_code AND r.relation_number = k.relation_number, e
  WHERE k.maand > e.eind - INTERVAL '12 months' AND k.maand <= e.eind AND NULLIF(r.zoek,'') IS NOT NULL
),
w AS (
  SELECT zoek, COUNT(DISTINCT admin_code) AS n_lob, SUM(omzet) AS omzet,
    STRING_AGG(DISTINCT CASE WHEN admin_code='alaw' THEN naam || ' (' || COALESCE(postcode,'') || ')' END, ' | ') AS awc,
    STRING_AGG(DISTINCT CASE WHEN admin_code='pgl1' THEN naam || ' (' || COALESCE(postcode,'') || ')' END, ' | ') AS afc,
    STRING_AGG(DISTINCT CASE WHEN admin_code='acco' THEN naam || ' (' || COALESCE(postcode,'') || ')' END, ' | ') AS acc
  FROM km GROUP BY zoek HAVING SUM(omzet) > 0
)
SELECT w.zoek, w.awc, w.afc, w.acc, ROUND(w.omzet) AS omzet_12m
FROM w
LEFT JOIN (SELECT DISTINCT zoek FROM "My Queries".klant_koppeltabel_lob WHERE n_lob = 3) rev ON rev.zoek = w.zoek
LEFT JOIN (SELECT DISTINCT zoek FROM "My Queries".kpi_triple_lob_beoordeling) beo ON beo.zoek = w.zoek
WHERE w.n_lob = 3 AND rev.zoek IS NULL AND beo.zoek IS NULL
