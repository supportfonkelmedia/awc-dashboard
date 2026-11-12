-- Peliqan "My Queries".kpi_kosten_maand (table_id 1418999), stand 2026-11-12
WITH b AS (
  SELECT admin_code, account_number,
    MAKE_DATE(CAST(book_year AS int),
      CASE WHEN 2000 + CAST(LEFT(book_period,2) AS int) < CAST(book_year AS int) THEN 1
           WHEN 2000 + CAST(LEFT(book_period,2) AS int) > CAST(book_year AS int) THEN 12
           WHEN RIGHT(book_period,2) = '00' THEN 1 WHEN RIGHT(book_period,2) > '12' THEN 12
           ELSE CAST(RIGHT(book_period,2) AS int) END, 1) AS maand,
    CAST(REPLACE(amount,',','.') AS numeric) AS bedrag
  FROM cashweb.ledger_mutations
  WHERE admin_code IN ('alaw','pgl1','acco') AND book_year >= '2024' AND book_year <= TO_CHAR(CURRENT_DATE, 'YYYY')
    AND LEFT(account_number,1) IN ('4','5','6','7','8') AND LEFT(account_number,2) NOT IN ('42','47','49')
),
g AS (
  SELECT admin_code, maand,
    CASE
      WHEN LEFT(account_number,1) = '8' THEN '1 Omzet'
      WHEN LEFT(account_number,1) IN ('6','7') THEN '2 Inkoop en directe kosten'
      WHEN LEFT(account_number,4) = '4517' THEN '4 Uitzendkrachten'
      WHEN LEFT(account_number,2) IN ('40','41') THEN '3 Eigen personeel (lonen, sociale lasten, salarisadministratie)'
      WHEN LEFT(account_number,3) = '453' THEN '5 Huisvesting (huur, servicekosten, parkeren)'
      WHEN LEFT(account_number,3) = '456' THEN '6 Huur machines en materieel'
      ELSE '7 Overige bedrijfskosten'
    END AS groep,
    bedrag
  FROM b
)
SELECT admin_code AS scope_code,
  CASE admin_code WHEN 'alaw' THEN 'AWC' WHEN 'pgl1' THEN 'AFC' ELSE 'ACC' END AS scope_label,
  maand, groep,
  ROUND(CASE WHEN groep = '1 Omzet' THEN -SUM(bedrag) ELSE SUM(bedrag) END) AS bedrag,
  (maand <= CAST(DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months' AS date)) AS afgesloten
FROM g
GROUP BY admin_code, maand, groep
