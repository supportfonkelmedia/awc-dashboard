-- Peliqan "My Queries".kpi_omzetbrug_klant (table_id 1416722), stand 2026-11-12
WITH r AS (
  SELECT
    admin_code,
    TRIM(relation_number) AS relation_number,
    MIN(UPPER(REGEXP_REPLACE(TRIM(search_name), '[^A-Za-z0-9]', '', 'g'))) AS zoek,
    MIN(TRIM(name)) AS naam
  FROM cashweb.relation
  WHERE
    admin_code IN ('alaw', 'pgl1', 'acco')
  GROUP BY
    1,
    2
), e AS (
  SELECT
    CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '2 MONTHS' AS DATE) AS eind
), k AS (
  SELECT
    km.entiteit,
    km.maand,
    km.omzet,
    CASE
      WHEN NULLIF(r.zoek, '') IS NULL OR b.status = 'afgekeurd'
      THEN km.admin_code || ':' || km.relation_number
      ELSE r.zoek
    END AS klant,
    COALESCE(r.naam, km.relation_number) AS naam,
    CASE
      WHEN km.maand > e.eind - INTERVAL '12 MONTHS' AND km.maand <= e.eind
      THEN 'nu'
      WHEN km.maand > e.eind - INTERVAL '24 MONTHS'
      AND km.maand <= e.eind - INTERVAL '12 MONTHS'
      THEN 'vorig'
    END AS periode
  FROM "My Queries".kpi_klant_omzet_maand AS km
  CROSS JOIN e
  LEFT JOIN r
    ON r.admin_code = km.admin_code AND r.relation_number = km.relation_number
  LEFT JOIN "My Queries".kpi_triple_lob_beoordeling AS b
    ON b.zoek = r.zoek
  LEFT JOIN "My Queries".kpi_intercompany AS ic
    ON ic.admin_code = km.admin_code AND ic.zoek = r.zoek
  WHERE
    ic.zoek IS NULL
), s AS (
  SELECT
    'Concern' AS scope,
    klant,
    MIN(naam) AS naam,
    STRING_AGG(DISTINCT entiteit, ', ') AS entiteiten,
    SUM(CASE WHEN periode = 'vorig' THEN omzet ELSE 0 END) AS vorig,
    SUM(CASE WHEN periode = 'nu' THEN omzet ELSE 0 END) AS nu
  FROM k
  WHERE
    NOT periode IS NULL
  GROUP BY
    klant
  UNION ALL
  SELECT
    entiteit,
    klant,
    MIN(naam) AS minNaam,
    MIN(entiteit) AS minEntiteit,
    SUM(CASE WHEN periode = 'vorig' THEN omzet ELSE 0 END) AS sumOmzetPeriode,
    SUM(CASE WHEN periode = 'nu' THEN omzet ELSE 0 END) AS sumOmzetPeriode
  FROM k
  WHERE
    NOT periode IS NULL
  GROUP BY
    entiteit,
    klant
)
SELECT
  s.scope,
  s.klant,
  s.naam,
  s.entiteiten,
  ROUND(s.vorig) AS omzet_vorig,
  ROUND(s.nu) AS omzet_nu,
  ROUND(s.nu - s.vorig) AS verschil,
  CASE
    WHEN vorig <= 0 AND nu > 0
    THEN 'nieuw'
    WHEN vorig > 0 AND nu <= 0
    THEN 'verloren'
    WHEN nu > vorig
    THEN 'gegroeid'
    WHEN nu < vorig
    THEN 'gekrompen'
    ELSE 'gelijk'
  END AS component,
  RANK() OVER (PARTITION BY s.scope ORDER BY s.nu - s.vorig DESC) AS rang_groei,
  RANK() OVER (PARTITION BY s.scope ORDER BY s.nu - s.vorig ASC) AS rang_krimp,
  MAX(e.eind) OVER () AS stand_per
FROM s
CROSS JOIN e
WHERE
  s.vorig > 0 OR s.nu > 0
