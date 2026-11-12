-- Peliqan "My Queries".kpi_bm_tegel (table_id 1416338), stand 2026-11-12 na jaarwisselingsfix: venster vanaf vorig jaar, sommen per jaar van de laatste afgesloten maand. Vorige versie: commit 66cd6a6.
WITH m AS (
  SELECT
    *
  FROM "My Queries".kpi_bm_maand
  WHERE
    maand >= DATE_TRUNC('YEAR', CURRENT_DATE) - INTERVAL '1 YEAR'
), eerste_open AS (
  SELECT
    admin_code,
    MIN(maand) AS eerste_open_maand
  FROM m
  WHERE
    maandstatus <> 'afgesloten'
  GROUP BY
    admin_code
), per_ent AS (
  SELECT
    m.admin_code,
    m.entiteit,
    COALESCE(MIN(e.eerste_open_maand) - INTERVAL '1 MONTH', MAX(m.maand)) AS t_m
  FROM m
  LEFT JOIN eerste_open AS e
    ON e.admin_code = m.admin_code
  GROUP BY
    m.admin_code,
    m.entiteit
), scope AS (
  SELECT
    admin_code,
    entiteit,
    CAST(t_m AS DATE) AS t_m
  FROM per_ent
  UNION ALL
  SELECT
    'concern' AS literal,
    'Concern (AWC, AFC, ACC)' AS literal,
    CAST(MIN(t_m) AS DATE) AS castT_M
  FROM per_ent
), calc AS (
  SELECT
    s.admin_code,
    s.entiteit,
    s.t_m,
    SUM(CASE WHEN m.maand <= s.t_m AND DATE_TRUNC('YEAR', m.maand) = DATE_TRUNC('YEAR', s.t_m) THEN m.bruto_marge END) AS bm_ytd,
    SUM(CASE WHEN m.maand <= s.t_m AND DATE_TRUNC('YEAR', m.maand) = DATE_TRUNC('YEAR', s.t_m) THEN m.loonkosten END) AS lk_ytd,
    SUM(CASE WHEN m.maand <= s.t_m AND DATE_TRUNC('YEAR', m.maand) = DATE_TRUNC('YEAR', s.t_m) THEN m.inhuur END) AS inhuur_ytd,
    SUM(CASE WHEN m.maand <= s.t_m AND DATE_TRUNC('YEAR', m.maand) = DATE_TRUNC('YEAR', s.t_m) THEN m.loon_deels END) AS loon_deels_ytd,
    SUM(CASE WHEN m.maand <= s.t_m - INTERVAL '1 MONTH' AND DATE_TRUNC('YEAR', m.maand) = DATE_TRUNC('YEAR', s.t_m - INTERVAL '1 MONTH') THEN m.bruto_marge END) AS bm_vorig,
    SUM(CASE WHEN m.maand <= s.t_m - INTERVAL '1 MONTH' AND DATE_TRUNC('YEAR', m.maand) = DATE_TRUNC('YEAR', s.t_m - INTERVAL '1 MONTH') THEN m.loonkosten END) AS lk_vorig,
    COUNT(DISTINCT CASE WHEN m.maand <= s.t_m AND DATE_TRUNC('YEAR', m.maand) = DATE_TRUNC('YEAR', s.t_m) THEN m.maand END) AS n_maanden,
    MAX(m.laatst_gesynct) AS bron_bijgewerkt
  FROM scope AS s
  JOIN m
    ON (
      s.admin_code = 'concern' OR m.admin_code = s.admin_code
    )
  GROUP BY
    s.admin_code,
    s.entiteit,
    s.t_m
)
SELECT
  'bruto_marge_per_loonkosten' AS kpi_code,
  admin_code AS scope_code,
  entiteit AS scope_label,
  CASE WHEN n_maanden >= 1 AND lk_ytd > 0 THEN ROUND(bm_ytd / lk_ytd, 2) END AS waarde,
  CASE WHEN n_maanden >= 2 AND lk_vorig > 0 THEN ROUND(bm_vorig / lk_vorig, 2) END AS waarde_vorige_maand,
  CASE
    WHEN n_maanden >= 2 AND lk_vorig > 0 AND lk_ytd > 0
    THEN ROUND(bm_ytd / lk_ytd - bm_vorig / lk_vorig, 2)
  END AS delta,
  ROUND(bm_ytd, 0) AS bruto_marge_ytd,
  ROUND(lk_ytd, 0) AS loonkosten_ytd,
  ROUND(inhuur_ytd, 0) AS waarvan_inhuur_4517,
  ROUND(loon_deels_ytd, 0) AS waarvan_deels_loon_4130_4512,
  n_maanden,
  'Kalenderjaar t/m ' || TO_CHAR(t_m, 'MM-YYYY') || ', alleen afgesloten maanden' AS venster,
  t_m AS stand_per,
  bron_bijgewerkt,
  CAST(NULL AS DECIMAL) AS doel,
  CAST(NULL AS TEXT) AS status,
  'geen doel ingesteld' AS doel_tekst,
  CASE
    WHEN admin_code = 'concern'
    THEN 'Concern loopt t/m de laatste maand die bij AWC, AFC en ACC is afgesloten. Alleen entiteiten met eigen personeel tellen mee.'
    ELSE NULL
  END AS toelichting
FROM calc
