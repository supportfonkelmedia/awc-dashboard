-- Peliqan "My Queries".klant_koppeltabel_lob (table_id 1361203), stand 2026-11-12
WITH klanten AS (
  SELECT DISTINCT r.admin_code,
         TRIM(r.relation_number) AS relation_number,
         TRIM(r.name) AS naam,
         UPPER(REGEXP_REPLACE(TRIM(r.search_name), '[^A-Za-z0-9]', '', 'g')) AS zoek,
         UPPER(REPLACE(TRIM(COALESCE(r.postal_code,'')), ' ', '')) AS pc,
         TRIM(COALESCE(r.country_code,'')) AS land
  FROM cashweb.relation r
  JOIN (
    SELECT DISTINCT admin_code, TRIM(relation_number) AS rn
    FROM cashweb.ledger_mutations
    WHERE admin_code IN ('alaw','acco','pgl1')
      AND LEFT(account_number,2) = '12'
      AND book_year IN ('2024','2025')
      AND NULLIF(TRIM(relation_number),'') IS NOT NULL
  ) m ON m.admin_code = r.admin_code AND m.rn = TRIM(r.relation_number)
  WHERE NULLIF(TRIM(r.search_name),'') IS NOT NULL
),
per_klant AS (
  SELECT zoek,
         COUNT(DISTINCT admin_code) AS n_lob,
         MIN(naam) AS naam,
         STRING_AGG(DISTINCT CASE WHEN admin_code='alaw' THEN relation_number END, ',') AS nr_alaw,
         STRING_AGG(DISTINCT CASE WHEN admin_code='pgl1' THEN relation_number END, ',') AS nr_pgl1,
         STRING_AGG(DISTINCT CASE WHEN admin_code='acco' THEN relation_number END, ',') AS nr_acco,
         COUNT(DISTINCT pc) AS n_postcodes,
         STRING_AGG(DISTINCT land, ',') AS landen
  FROM klanten
  GROUP BY zoek
)
SELECT zoek,
       naam,
       n_lob,
       nr_alaw, nr_pgl1, nr_acco,
       CASE
         WHEN n_lob < 3 THEN NULL
         WHEN zoek IN ('DISTILLERS','DUTCH','GOOD','HOXTON','MAX','SPIRITS') THEN 'afgekeurd'
         WHEN zoek IN ('ALFA','COMPAGNIA','DASH','ESSPO','RIGHT','TECAN') THEN 'concern'
         ELSE 'zeker'
       END AS zekerheid,
       CASE
         WHEN LENGTH(zoek) < 6 AND n_lob > 1 AND n_postcodes > 1 THEN 'ja'
         ELSE 'nee'
       END AS controle_nodig,
       n_postcodes,
       landen
FROM per_klant
ORDER BY n_lob DESC, zoek
