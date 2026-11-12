-- Peliqan "My Queries".kpi_ebitda_tegel (table_id 1418996), stand 2026-11-12
WITH afgesl AS (
  SELECT
    admin_code,
    MAX(maand) AS laatste
  FROM "My Queries".kpi_bm_maand
  WHERE
    maandstatus = 'afgesloten'
  GROUP BY
    admin_code
), e AS (
  SELECT
    MIN(laatste) AS eind
  FROM afgesl
), nu AS (
  SELECT
    m.*
  FROM "My Queries".kpi_ebitda_maand AS m
  CROSS JOIN e
  WHERE
    m.maand = e.eind
), vorig AS (
  SELECT
    m.scope_code,
    m.ebitda_12m
  FROM "My Queries".kpi_ebitda_maand AS m
  CROSS JOIN e
  WHERE
    m.maand = CAST(e.eind - INTERVAL '12 MONTHS' AS DATE)
), om AS (
  SELECT
    m.scope_code,
    SUM(
      CASE
        WHEN m.maand > e.eind - INTERVAL '12 MONTHS' AND m.maand <= e.eind
        THEN m.omzet
        ELSE 0
      END
    ) AS omzet_nu,
    SUM(
      CASE
        WHEN m.maand > e.eind - INTERVAL '24 MONTHS' AND m.maand <= e.eind - INTERVAL '12 MONTHS'
        THEN m.omzet
        ELSE 0
      END
    ) AS omzet_vorig
  FROM "My Queries".kpi_ebitda_maand AS m
  CROSS JOIN e
  GROUP BY
    m.scope_code
)
SELECT
  'ebitda' AS kpi_code,
  nu.scope_code,
  nu.scope_label,
  nu.ebitda_12m AS waarde,
  v.ebitda_12m AS waarde_vorige,
  nu.ebitda_12m - v.ebitda_12m AS delta,
  CAST(nu.maanden_in_12m AS BIGINT) AS n,
  CAST(NULL AS TEXT) AS leeg_reden,
  'Twaalf afgesloten maanden t/m ' || TO_CHAR(nu.maand, 'MM-YYYY') || ' tegenover de twaalf daarvoor' AS venster,
  nu.maand AS stand_per,
  CURRENT_TIMESTAMP AS bron_bijgewerkt,
  'EBITDA-marge ' || ROUND(100.0 * nu.ebitda_12m / NULLIF(om.omzet_nu, 0), 1) || '% (was ' || ROUND(100.0 * v.ebitda_12m / NULLIF(om.omzet_vorig, 0), 1) || '%) bij een omzet van ' || ROUND(om.omzet_nu / 1000000.0, 2) || ' mln. Alleen maanden die voor alle drie de entiteiten zijn afgesloten; eindejaarsboekingen 2026 volgen nog.' AS toelichting
FROM nu
LEFT JOIN vorig AS v
  ON v.scope_code = nu.scope_code
LEFT JOIN om
  ON om.scope_code = nu.scope_code
