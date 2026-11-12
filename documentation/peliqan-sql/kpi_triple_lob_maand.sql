-- Peliqan "My Queries".kpi_triple_lob_maand (table_id 1416458), stand 2026-11-12
WITH r AS (
  SELECT
    admin_code,
    TRIM(relation_number) AS relation_number,
    MIN(UPPER(REGEXP_REPLACE(TRIM(search_name), '[^A-Za-z0-9]', '', 'g'))) AS zoek
  FROM cashweb.relation
  WHERE
    admin_code IN ('alaw', 'pgl1', 'acco')
  GROUP BY
    1,
    2
), km AS (
  SELECT
    k.admin_code,
    k.maand,
    k.omzet,
    COALESCE(NULLIF(r.zoek, ''), k.admin_code || ':' || k.relation_number) AS zoek
  FROM "My Queries".kpi_klant_omzet_maand AS k
  LEFT JOIN r
    ON r.admin_code = k.admin_code AND r.relation_number = k.relation_number
), e AS (
  SELECT
    CAST(GENERATE_SERIES(
      CAST('2025-01-01' AS DATE),
      CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '2 MONTHS' AS DATE),
      INTERVAL '1 MONTH'
    ) AS DATE) AS eind
), w AS (
  SELECT
    e.eind,
    km.zoek,
    COUNT(DISTINCT km.admin_code) AS n_lob,
    SUM(km.omzet) AS omzet
  FROM e
  JOIN km
    ON km.maand > e.eind - INTERVAL '12 MONTHS' AND km.maand <= e.eind
  GROUP BY
    1,
    2
  HAVING
    SUM(km.omzet) > 0
), rev AS (
  SELECT
    zoek,
    MIN(zekerheid) AS zekerheid
  FROM "My Queries".klant_koppeltabel_lob
  WHERE
    n_lob = 3
  GROUP BY
    zoek
), c AS (
  SELECT
    w.*,
    CASE
      WHEN w.n_lob < 3
      THEN NULL
      WHEN NOT b.status IS NULL
      THEN b.status
      WHEN rev.zekerheid = 'zeker'
      THEN 'zeker'
      ELSE 'te_controleren'
    END AS status
  FROM w
  LEFT JOIN rev
    ON rev.zoek = w.zoek
  LEFT JOIN "My Queries".kpi_triple_lob_beoordeling AS b
    ON b.zoek = w.zoek
)
SELECT
  eind AS maand,
  COUNT(*) AS klanten,
  COUNT(*) FILTER(WHERE
    status = 'zeker') AS triple_zeker,
  COUNT(*) FILTER(WHERE
    status = 'concern') AS triple_concern,
  COUNT(*) FILTER(WHERE
    status = 'te_controleren') AS triple_te_controleren,
  COUNT(*) FILTER(WHERE
    status = 'afgekeurd') AS triple_afgekeurd,
  ROUND(100.0 * COUNT(*) FILTER(WHERE
    status = 'zeker') / COUNT(*), 1) AS pct_klanten_zeker,
  ROUND(100.0 * COUNT(*) FILTER(WHERE
    status IN ('zeker', 'concern')) / COUNT(*), 1) AS pct_klanten_met_concern,
  ROUND(100.0 * SUM(omzet) FILTER(WHERE
    status = 'zeker') / SUM(omzet), 1) AS pct_omzet_zeker,
  ROUND(100.0 * SUM(omzet) FILTER(WHERE
    status IN ('zeker', 'concern')) / SUM(omzet), 1) AS pct_omzet_met_concern,
  ROUND(SUM(omzet) / 1000000, 2) AS omzet_mln
FROM c
GROUP BY
  eind
