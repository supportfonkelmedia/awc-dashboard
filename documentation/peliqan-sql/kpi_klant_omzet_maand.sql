-- Peliqan "My Queries".kpi_klant_omzet_maand (table_id 1416457), stand 2026-11-12
WITH lm AS (
  SELECT admin_code, TRIM(journal_code) AS dagboek, document_number, book_period, account_number,
    TRIM(relation_number) AS relation_number, amount
  FROM cashweb.ledger_mutations
  WHERE admin_code IN ('alaw','pgl1','acco') AND book_period >= '2401' AND book_period <= TO_CHAR(CURRENT_DATE, 'YY') || '12'
    AND (LEFT(account_number,1)='8' OR LEFT(account_number,2)='12')
),
doc AS (
  SELECT admin_code, dagboek, document_number, book_period,
    MIN(CASE WHEN LEFT(account_number,2)='12' AND relation_number <> '' THEN relation_number END) AS relation_number,
    -SUM(CASE WHEN LEFT(account_number,1)='8' AND account_number <> '802001' THEN CAST(REPLACE(amount,',','.') AS numeric) ELSE 0 END) AS omzet
  FROM lm
  GROUP BY 1,2,3,4
)
SELECT admin_code,
  CASE admin_code WHEN 'alaw' THEN 'AWC' WHEN 'pgl1' THEN 'AFC' ELSE 'ACC' END AS entiteit,
  relation_number,
  MAKE_DATE(2000 + CAST(LEFT(book_period,2) AS int), CAST(RIGHT(book_period,2) AS int), 1) AS maand,
  SUM(omzet) AS omzet
FROM doc
WHERE relation_number IS NOT NULL AND omzet <> 0
GROUP BY 1,2,3,4
