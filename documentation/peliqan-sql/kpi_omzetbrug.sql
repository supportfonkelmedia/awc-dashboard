-- Peliqan "My Queries".kpi_omzetbrug (table_id 1416464), stand 2026-11-12
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
    SUM(CASE WHEN periode = 'vorig' THEN omzet ELSE 0 END) AS sumOmzetPeriode,
    SUM(CASE WHEN periode = 'nu' THEN omzet ELSE 0 END) AS sumOmzetPeriode
  FROM k
  WHERE
    NOT periode IS NULL
  GROUP BY
    entiteit,
    klant
), c AS (
  SELECT
    s.*,
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
    END AS component
  FROM s
  WHERE
    vorig > 0 OR nu > 0
)
SELECT
  c.scope,
  x.volgorde,
  x.component,
  ROUND(
    CASE x.component
      WHEN 'start'
      THEN SUM(c.vorig)
      WHEN 'eind'
      THEN SUM(c.nu)
      ELSE SUM(CASE WHEN c.component = x.component THEN c.nu - c.vorig ELSE 0 END)
    END
  ) AS bedrag,
  CASE x.component
    WHEN 'start'
    THEN COUNT(*) FILTER(WHERE
      c.vorig > 0)
    WHEN 'eind'
    THEN COUNT(*) FILTER(WHERE
      c.nu > 0)
    ELSE COUNT(*) FILTER(WHERE
      c.component = x.component)
  END AS klanten,
  MAX(e.eind) AS stand_per
FROM c
CROSS JOIN (VALUES
  (1, 'start'),
  (2, 'nieuw'),
  (3, 'gegroeid'),
  (4, 'gekrompen'),
  (5, 'verloren'),
  (6, 'eind')) AS x(volgorde, component)
CROSS JOIN e
GROUP BY
  c.scope,
  x.volgorde,
  x.component
ORDER BY
  CASE c.scope WHEN 'Concern' THEN 0 WHEN 'AWC' THEN 1 WHEN 'AFC' THEN 2 ELSE 3 END,
  x.volgorde
