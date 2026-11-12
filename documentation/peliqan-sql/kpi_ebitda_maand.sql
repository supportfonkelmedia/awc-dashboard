-- Peliqan "My Queries".kpi_ebitda_maand (table_id 1418995), stand 2026-11-12
WITH b AS (
  SELECT
    admin_code,
    CAST(book_year AS INT) AS jaar,
    CASE
      WHEN 2000 + CAST(LEFT(book_period, 2) AS INT) < CAST(book_year AS INT)
      THEN 1
      WHEN 2000 + CAST(LEFT(book_period, 2) AS INT) > CAST(book_year AS INT)
      THEN 12
      WHEN RIGHT(book_period, 2) = '00'
      THEN 1
      WHEN RIGHT(book_period, 2) > '12'
      THEN 12
      ELSE CAST(RIGHT(book_period, 2) AS INT)
    END AS mnd,
    account_number,
    CAST(REPLACE(amount, ',', '.') AS DECIMAL) AS bedrag
  FROM cashweb.ledger_mutations
  WHERE
    admin_code IN ('alaw', 'pgl1', 'acco')
    AND book_year >= '2023' AND book_year <= TO_CHAR(CURRENT_DATE, 'YYYY')
    AND LEFT(account_number, 1) IN ('4', '5', '6', '7', '8')
    AND NOT LEFT(account_number, 2) IN ('42', '47', '49')
), m AS (
  SELECT
    admin_code,
    MAKE_DATE(jaar, mnd, 1) AS maand,
    -SUM(CASE WHEN LEFT(account_number, 1) = '8' THEN bedrag ELSE 0 END) AS omzet,
    -SUM(bedrag) AS ebitda
  FROM b
  GROUP BY
    1,
    2
), a AS (
  SELECT
    admin_code AS scope_code,
    CASE admin_code WHEN 'alaw' THEN 'AWC' WHEN 'pgl1' THEN 'AFC' ELSE 'ACC' END AS scope_label,
    maand,
    omzet,
    ebitda
  FROM m
  UNION ALL
  SELECT
    'concern' AS literal,
    'Concern (AWC, AFC, ACC)' AS literal,
    maand,
    SUM(omzet) AS sumOmzet,
    SUM(ebitda) AS sumEbitda
  FROM m
  GROUP BY
    maand
)
SELECT
  scope_code,
  scope_label,
  maand,
  ROUND(omzet) AS omzet,
  ROUND(ebitda) AS ebitda,
  ROUND(100.0 * ebitda / NULLIF(omzet, 0), 1) AS ebitda_marge_pct,
  ROUND(
    SUM(ebitda) OVER (PARTITION BY scope_code ORDER BY maand ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
  ) AS ebitda_12m,
  COUNT(*) OVER (PARTITION BY scope_code ORDER BY maand ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS maanden_in_12m,
  ROUND(
    SUM(ebitda) OVER (PARTITION BY scope_code, DATE_TRUNC('YEAR', maand) ORDER BY maand)
  ) AS ebitda_jaar_tot_nu,
  (
    maand <= CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '2 MONTHS' AS DATE)
  ) AS afgesloten
FROM a
