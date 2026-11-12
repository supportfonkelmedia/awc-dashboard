-- Peliqan "My Queries".kpi_trend (table_id 1419146), stand 2026-11-12 vóór de AFC-tegelwijziging
WITH bm AS (
  SELECT
    admin_code AS scope_code,
    maand,
    bruto_marge,
    loonkosten
  FROM "My Queries".kpi_bm_maand
  WHERE
    maandstatus = 'afgesloten' AND maand >= CAST('2025-01-01' AS DATE)
), bm_c AS (
  SELECT
    'concern' AS scope_code,
    maand,
    SUM(bruto_marge) AS bruto_marge,
    SUM(loonkosten) AS loonkosten
  FROM bm
  GROUP BY
    maand
  HAVING
    COUNT(*) = 3
), bm_all AS (
  SELECT
    *
  FROM bm
  UNION ALL
  SELECT
    *
  FROM bm_c
), t_bm AS (
  SELECT
    'bruto_marge_per_loonkosten' AS kpi_code,
    scope_code,
    CAST(NULL AS TEXT) AS serie,
    maand AS periode,
    ROUND(
      SUM(bruto_marge) OVER (PARTITION BY scope_code, DATE_TRUNC('YEAR', maand) ORDER BY maand) / NULLIF(
        SUM(loonkosten) OVER (PARTITION BY scope_code, DATE_TRUNC('YEAR', maand) ORDER BY maand),
        0
      ),
      2
    ) AS waarde,
    'definitief' AS status
  FROM bm_all
), t_tlob AS (
  SELECT
    'triple_lob' AS literal,
    'concern' AS literal,
    CAST(NULL AS TEXT) AS cast,
    maand,
    pct_klanten_zeker,
    'definitief' AS literal
  FROM "My Queries".kpi_triple_lob_maand
), t_win AS (
  SELECT
    'winrate' AS literal,
    pipeline,
    CAST(NULL AS TEXT) AS cast,
    peildatum,
    ROUND(100.0 * gewonnen / NULLIF(gewonnen + verloren, 0), 1) AS roundGewonnenGewonnenVerloren,
    CASE WHEN soort = 'maandeinde' THEN 'definitief' ELSE 'voorlopig' END AS caseSoort
  FROM "My Queries".kpi_winrate_maand
), t_churn AS (
  SELECT
    'churn' AS literal,
    'concern' AS literal,
    CAST(NULL AS TEXT) AS cast,
    kwartaal,
    CAST(vertrokken AS DECIMAL) AS castVertrokken,
    CASE WHEN lopend_kwartaal THEN 'voorlopig' ELSE 'definitief' END AS caseLopend_Kwartaal
  FROM "My Queries".kpi_churn_kwartaal
), rel AS (
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
), om AS (
  SELECT
    km.admin_code AS scope_code,
    km.maand,
    SUM(km.omzet) AS omzet
  FROM "My Queries".kpi_klant_omzet_maand AS km
  LEFT JOIN rel AS r
    ON r.admin_code = km.admin_code AND r.relation_number = km.relation_number
  LEFT JOIN "My Queries".kpi_intercompany AS ic
    ON ic.admin_code = km.admin_code AND ic.zoek = r.zoek
  WHERE
    ic.zoek IS NULL
  GROUP BY
    1,
    2
), om_all AS (
  SELECT
    *
  FROM om
  UNION ALL
  SELECT
    'concern' AS literal,
    maand,
    SUM(omzet) AS sumOmzet
  FROM om
  GROUP BY
    maand
), brug_eind AS (
  SELECT
    MAX(stand_per) AS eind
  FROM "My Queries".kpi_omzetbrug
), t_brug AS (
  SELECT
    'omzet_brug' AS literal,
    o.scope_code,
    CAST(NULL AS TEXT) AS cast,
    o.maand,
    ROUND(
      SUM(o.omzet) OVER (PARTITION BY o.scope_code ORDER BY o.maand ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
    ) AS roundScope_CodeOmzetMaand,
    CASE WHEN o.maand <= b.eind THEN 'definitief' ELSE 'voorlopig' END AS caseMaandEind
  FROM om_all AS o
  CROSS JOIN brug_eind AS b
), ebitda_eind AS (
  SELECT
    MIN(laatste) AS eind
  FROM (
    SELECT
      admin_code,
      MAX(maand) AS laatste
    FROM "My Queries".kpi_bm_maand
    WHERE
      maandstatus = 'afgesloten'
    GROUP BY
      admin_code
  ) AS x
), t_ebitda AS (
  SELECT
    'ebitda' AS literal,
    m.scope_code,
    CAST(NULL AS TEXT) AS cast,
    m.maand,
    m.ebitda_12m,
    CASE WHEN m.maand <= e.eind THEN 'definitief' ELSE 'voorlopig' END AS caseMaandEind
  FROM "My Queries".kpi_ebitda_maand AS m
  CROSS JOIN ebitda_eind AS e
), t_d2s AS (
  SELECT
    'dock_to_stock' AS literal,
    'alaw' AS literal,
    CAST(NULL AS TEXT) AS cast,
    maand,
    pct_binnen_24u,
    CASE WHEN afgesloten THEN 'definitief' ELSE 'voorlopig' END AS caseAfgesloten
  FROM "My Queries".kpi_d2s_maand
), t_ops AS (
  SELECT
    'damage_rate' AS literal,
    'alaw' AS literal,
    CAST(NULL AS TEXT) AS cast,
    maand,
    pct_beschadigd_geleverd,
    CASE WHEN afgesloten THEN 'definitief' ELSE 'voorlopig' END AS caseAfgesloten
  FROM "My Queries".kpi_awc_ops_maand
  UNION ALL
  SELECT
    'throughput' AS literal,
    'alaw' AS literal,
    CAST(NULL AS TEXT) AS cast,
    maand,
    CAST(outbound_orders AS DECIMAL) AS castOutbound_Orders,
    CASE WHEN afgesloten THEN 'definitief' ELSE 'voorlopig' END AS caseAfgesloten
  FROM "My Queries".kpi_awc_ops_maand
), t_acc AS (
  SELECT
    'acc_dossiers' AS literal,
    'acco' AS literal,
    soort,
    maand,
    CAST(dossiers AS DECIMAL) AS castDossiers,
    CASE WHEN lopende_maand THEN 'voorlopig' ELSE 'definitief' END AS caseLopende_Maand
  FROM "My Queries".kpi_acc_dossiers_maand
  UNION ALL
  SELECT
    'acc_doorlooptijd' AS literal,
    'acco' AS literal,
    CAST(NULL AS TEXT) AS cast,
    maand,
    mediaan_dagen,
    CASE WHEN lopende_maand THEN 'voorlopig' ELSE 'definitief' END AS caseLopende_Maand
  FROM "My Queries".kpi_acc_doorlooptijd_maand
), t_onb AS (
  SELECT
    'time_to_onboarding' AS literal,
    CASE pijplijn
      WHEN 'AWC'
      THEN 'alaw'
      WHEN 'AFC'
      THEN 'pgl1'
      WHEN 'ACC'
      THEN 'acco'
      ELSE pijplijn
    END AS casePijplijnPijplijn,
    CAST(NULL AS TEXT) AS cast,
    kwartaal,
    mediaan_dagen,
    CASE WHEN lopend_kwartaal THEN 'voorlopig' ELSE 'definitief' END AS caseLopend_Kwartaal
  FROM "My Queries".kpi_onboarding_kwartaal
), t_spr AS (
  SELECT
    'afc_zendingen' AS literal,
    'pgl1' AS literal,
    CAST(NULL AS TEXT) AS cast,
    maand,
    CAST(zendingen AS DECIMAL) AS castZendingen,
    CASE
      WHEN status = 'volledig'
      THEN 'definitief'
      WHEN status = 'voorlopig'
      THEN 'voorlopig'
      ELSE 'onvolledig'
    END AS caseStatusStatus
  FROM "My Queries".kpi_afc_sprinter_maand
  UNION ALL
  SELECT
    'afc_modal_split' AS literal,
    'pgl1' AS literal,
    'pct_weg' AS literal,
    maand,
    pct_weg,
    CASE
      WHEN status = 'volledig'
      THEN 'definitief'
      WHEN status = 'voorlopig'
      THEN 'voorlopig'
      ELSE 'onvolledig'
    END AS caseStatusStatus
  FROM "My Queries".kpi_afc_sprinter_maand
  UNION ALL
  SELECT
    'afc_marge_per_zending' AS literal,
    'pgl1' AS literal,
    CAST(NULL AS TEXT) AS cast,
    maand,
    marge_per_zending,
    CASE
      WHEN status = 'volledig'
      THEN 'definitief'
      WHEN status = 'voorlopig'
      THEN 'voorlopig'
      ELSE 'onvolledig'
    END AS caseStatusStatus
  FROM "My Queries".kpi_afc_sprinter_maand
), alles AS (
  SELECT
    *
  FROM t_bm
  UNION ALL
  SELECT
    *
  FROM t_tlob
  UNION ALL
  SELECT
    *
  FROM t_win
  UNION ALL
  SELECT
    *
  FROM t_churn
  UNION ALL
  SELECT
    *
  FROM t_brug
  UNION ALL
  SELECT
    *
  FROM t_ebitda
  UNION ALL
  SELECT
    *
  FROM t_d2s
  UNION ALL
  SELECT
    *
  FROM t_ops
  UNION ALL
  SELECT
    *
  FROM t_acc
  UNION ALL
  SELECT
    *
  FROM t_onb
  UNION ALL
  SELECT
    *
  FROM t_spr
)
SELECT
  kpi_code,
  scope_code,
  COALESCE(serie, '') AS serie,
  periode,
  waarde,
  status,
  ROW_NUMBER() OVER (PARTITION BY kpi_code, scope_code, serie ORDER BY periode) AS volgnummer
FROM alles
WHERE
  periode >= CAST('2024-12-01' AS DATE) AND NOT waarde IS NULL
