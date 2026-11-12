-- Peliqan "My Queries".kpi_omzet_lob (table_id 1416720), stand 2026-11-12
WITH m AS (
  SELECT admin_code,
    MAKE_DATE(2000 + CAST(LEFT(book_period,2) AS int), CAST(RIGHT(book_period,2) AS int), 1) AS maand,
    -SUM(CAST(REPLACE(amount,',','.') AS numeric)) AS omzet
  FROM cashweb.ledger_mutations
  WHERE admin_code IN ('alaw','pgl1','acco') AND book_year >= '2024' AND book_year <= TO_CHAR(CURRENT_DATE, 'YYYY')
    AND LEFT(account_number,1)='8' AND account_number <> '802001'
    AND RIGHT(book_period,2) BETWEEN '01' AND '12'
  GROUP BY 1,2
),
a AS (
  SELECT admin_code AS scope_code,
    CASE admin_code WHEN 'alaw' THEN 'AWC' WHEN 'pgl1' THEN 'AFC' ELSE 'ACC' END AS scope_label,
    maand, omzet FROM m
  UNION ALL
  SELECT 'concern', 'Concern (AWC, AFC, ACC)', maand, SUM(omzet) FROM m GROUP BY maand
)
SELECT a.scope_code, a.scope_label, a.maand, ROUND(a.omzet) AS omzet,
  ROUND(v.omzet) AS omzet_vorig_jaar,
  CASE WHEN v.omzet > 0 THEN ROUND(100.0 * (a.omzet - v.omzet) / v.omzet, 1) END AS delta_pct,
  ROUND(SUM(a.omzet) OVER (PARTITION BY a.scope_code, DATE_TRUNC('year', a.maand) ORDER BY a.maand)) AS omzet_jaar_tot_nu,
  (a.maand <= CAST(DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months' AS date)) AS afgesloten
FROM a
LEFT JOIN a v ON v.scope_code = a.scope_code AND v.maand = CAST(a.maand - INTERVAL '12 months' AS date)
