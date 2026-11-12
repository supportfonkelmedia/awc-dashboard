-- Peliqan "My Queries".kpi_bm_maand (table_id 1416337), stand 2026-11-12
WITH ent AS (
  SELECT * FROM (VALUES ('alaw','AWC',0),('pgl1','AFC',1),('acco','ACC',0)) v(admin_code, entiteit, extra_lag)
),
mut AS (
  SELECT m.admin_code,
         MAKE_DATE(2000 + CAST(LEFT(m.book_period,2) AS int), CAST(RIGHT(m.book_period,2) AS int), 1) AS maand,
         m.account_number,
         CAST(REPLACE(m.amount, ',', '.') AS numeric) AS bedrag,
         m._sdc_batched_at
  FROM cashweb.ledger_mutations m
  WHERE m.admin_code IN ('alaw','pgl1','acco')
    AND m.book_period ~ '^[0-9]{4}$'
    AND RIGHT(m.book_period,2) BETWEEN '01' AND '12'
    AND LEFT(m.account_number,1) IN ('4','6','8')
),
per_maand AS (
  SELECT u.admin_code, u.maand,
    SUM(CASE WHEN LEFT(u.account_number,1)='8' THEN -u.bedrag ELSE 0 END) AS omzet,
    SUM(CASE WHEN LEFT(u.account_number,1)='6' THEN u.bedrag ELSE 0 END) AS inkoop,
    SUM(CASE WHEN r.rol='loon' THEN u.bedrag ELSE 0 END) AS loon,
    SUM(CASE WHEN r.rol='loon_deels' THEN u.bedrag ELSE 0 END) AS loon_deels,
    SUM(CASE WHEN r.rol='inhuur' THEN u.bedrag ELSE 0 END) AS inhuur,
    MAX(u._sdc_batched_at) AS laatst_gesynct
  FROM mut u
  LEFT JOIN "My Queries".kpi_bm_rekeningen r
    ON r.admin_code = u.admin_code AND r.account_number = u.account_number
  WHERE u.maand < DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY u.admin_code, u.maand
),
getoetst AS (
  SELECT p.*, e.entiteit, e.extra_lag,
    p.omzet - p.inkoop AS bruto_marge,
    p.loon + p.loon_deels + p.inhuur AS loonkosten,
    AVG(p.loon + p.loon_deels) OVER (PARTITION BY p.admin_code ORDER BY p.maand ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING) AS loon_gem_3m
  FROM per_maand p JOIN ent e ON e.admin_code = p.admin_code
)
SELECT admin_code, entiteit, maand,
  ROUND(omzet,0) AS omzet, ROUND(inkoop,0) AS inkoop, ROUND(bruto_marge,0) AS bruto_marge,
  ROUND(loon,0) AS loon, ROUND(loon_deels,0) AS loon_deels, ROUND(inhuur,0) AS inhuur, ROUND(loonkosten,0) AS loonkosten,
  CASE WHEN loonkosten > 0 THEN ROUND(bruto_marge / loonkosten, 2) END AS ratio_maand,
  CASE
    WHEN maand > (DATE_TRUNC('month', CURRENT_DATE) - (1 + extra_lag) * INTERVAL '1 month') THEN 'nog niet afgesloten (wachttijd entiteit)'
    WHEN loon_gem_3m IS NOT NULL AND (loon + loon_deels) < 0.5 * loon_gem_3m THEN 'loon nog niet geboekt'
    ELSE 'afgesloten'
  END AS maandstatus,
  laatst_gesynct
FROM getoetst
