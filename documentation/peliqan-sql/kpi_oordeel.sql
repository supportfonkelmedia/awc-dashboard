-- Peliqan "My Queries".kpi_oordeel (table_id 1416385), stand 2026-11-12: join op kpi_betrouwbaarheid (fase 0) en eigenaar per scope voor omzet_brug (v1 22-09: AWC Mark, AFC Floor, ACC Mesut). Vorige versie: commit 91d3f66.
WITH tegels AS (
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige_maand,
    delta,
    n_maanden AS n,
    CAST(NULL AS TEXT) AS leeg_reden,
    venster AS venster_tekst,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_bm_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige_maand,
    delta_procentpunt,
    CAST(n_beslist AS BIGINT) AS castN_Beslist,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_winrate_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige,
    delta,
    n,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_hs_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige,
    delta,
    n,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_triple_lob_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige,
    delta,
    n,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_omzetbrug_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige,
    delta,
    n,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_d2s_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige,
    delta,
    n,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_ebitda_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige,
    delta,
    n,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_awc_ops_tegel
  UNION ALL
  SELECT
    kpi_code,
    scope_code,
    scope_label,
    waarde,
    waarde_vorige,
    delta,
    n,
    leeg_reden,
    venster,
    stand_per,
    bron_bijgewerkt,
    toelichting
  FROM "My Queries".kpi_afc_sprinter_tegel
  UNION ALL
  SELECT
    h.kpi_code,
    h.scope_code,
    h.scope_code,
    h.waarde,
    LAG(h.waarde) OVER (PARTITION BY h.kpi_code, h.scope_code ORDER BY h.periode_einde) AS windowKpi_CodeScope_CodeWaardePeriode_Einde,
    h.waarde - LAG(h.waarde) OVER (PARTITION BY h.kpi_code, h.scope_code ORDER BY h.periode_einde) AS subWaardeKpi_CodeScope_CodeWaardePeriode_Einde,
    CAST(h.n AS BIGINT) AS castN,
    CAST(NULL AS TEXT) AS cast,
    'Handmatig ingevoerd' AS literal,
    h.periode_einde,
    h.ingevoerd_op,
    h.opmerking
  FROM "My Queries".kpi_handmatig AS h
  WHERE
    h.kpi_code <> 'ebitda'
), handmatig_laatste AS (
  SELECT
    kpi_code,
    scope_code,
    MAX(stand_per) AS laatste
  FROM tegels
  WHERE
    venster_tekst = 'Handmatig ingevoerd'
  GROUP BY
    kpi_code,
    scope_code
), tegels_actueel AS (
  SELECT
    t.*
  FROM tegels AS t
  LEFT JOIN handmatig_laatste AS hl
    ON hl.kpi_code = t.kpi_code AND hl.scope_code = t.scope_code
  WHERE
    t.venster_tekst <> 'Handmatig ingevoerd' OR t.stand_per = hl.laatste
  UNION ALL
  SELECT
    r.kpi_code,
    'concern' AS scope_code,
    'Concern' AS scope_label,
    CAST(NULL AS NUMERIC) AS waarde,
    CAST(NULL AS NUMERIC) AS waarde_vorige_maand,
    CAST(NULL AS NUMERIC) AS delta,
    CAST(NULL AS BIGINT) AS n,
    CAST(NULL AS TEXT) AS leeg_reden,
    CAST(NULL AS TEXT) AS venster_tekst,
    CAST(NULL AS DATE) AS stand_per,
    CAST(NULL AS TIMESTAMP WITH TIME ZONE) AS bron_bijgewerkt,
    CAST(NULL AS TEXT) AS toelichting
  FROM "My Queries".kpi_registry AS r
  WHERE
    r.bouwstatus = 'handmatig'
    AND NOT EXISTS (
      SELECT 1 FROM tegels AS t2 WHERE t2.kpi_code = r.kpi_code AND t2.scope_code = 'concern'
    )
), doel_actueel AS (
  SELECT DISTINCT ON (kpi_code, scope_code)
    kpi_code,
    scope_code,
    doel,
    marge_bijna
  FROM "My Queries".kpi_doelen
  WHERE
    geldig_vanaf <= CURRENT_DATE
  ORDER BY
    kpi_code,
    scope_code,
    geldig_vanaf DESC
), betr AS (
  SELECT
    kpi_code,
    scope_code,
    niveau,
    reden
  FROM "My Queries".kpi_betrouwbaarheid
), eigenaar_scope AS (
  SELECT
    *
  FROM (VALUES
    ('omzet_brug', 'alaw', 'Mark'),
    ('omzet_brug', 'pgl1', 'Floor'),
    ('omzet_brug', 'acco', 'Mesut')
  ) AS v(kpi_code, scope_code, eigenaar)
)
SELECT
  r.volgorde,
  r.kpi_code,
  r.naam,
  r.niveau,
  r.pijler,
  COALESCE(es.eigenaar, r.eigenaar) AS eigenaar,
  r.validator,
  r.bron,
  r.eenheid,
  r.richting,
  r.bouwstatus,
  t.scope_code,
  t.scope_label,
  CASE
    WHEN COALESCE(bs.niveau, ba.niveau) = 'onbetrouwbaar'
    THEN NULL
    WHEN r.bouwstatus IN ('live', 'handmatig') AND COALESCE(t.n, 0) >= r.min_n
    THEN t.waarde
  END AS waarde,
  CASE WHEN r.bouwstatus IN ('live', 'handmatig') AND COALESCE(bs.niveau, ba.niveau, '') <> 'onbetrouwbaar' THEN t.waarde_vorige_maand END AS waarde_vorige,
  CASE WHEN r.bouwstatus IN ('live', 'handmatig') AND COALESCE(bs.niveau, ba.niveau, '') <> 'onbetrouwbaar' THEN t.delta END AS delta,
  t.n,
  r.min_n,
  d.doel,
  CASE WHEN NOT d.doel IS NULL AND NOT t.waarde IS NULL THEN t.waarde - d.doel END AS afstand_tot_doel,
  CASE
    WHEN d.doel IS NULL OR t.waarde IS NULL OR NOT r.bouwstatus IN ('live', 'handmatig') OR COALESCE(bs.niveau, ba.niveau) = 'onbetrouwbaar'
    THEN NULL
    WHEN (
      r.richting = 'hoger_beter' AND t.waarde >= d.doel
    )
    OR (
      r.richting = 'lager_beter' AND t.waarde <= d.doel
    )
    THEN 'op_doel'
    WHEN NOT d.marge_bijna IS NULL AND ABS(t.waarde - d.doel) <= d.marge_bijna
    THEN 'bijna'
    ELSE 'onder_doel'
  END AS status,
  CASE
    WHEN r.bouwstatus = 'gepland_2027'
    THEN 'gepland_2027'
    WHEN r.bouwstatus = 'tbd'
    THEN 'tbd'
    WHEN r.bouwstatus = 'in_ontwikkeling'
    THEN 'in_ontwikkeling'
    WHEN COALESCE(bs.niveau, ba.niveau) = 'onbetrouwbaar'
    THEN 'onbetrouwbaar'
    WHEN r.bouwstatus = 'handmatig' AND t.waarde IS NULL
    THEN 'wacht_op_invoer'
    WHEN t.waarde IS NULL OR COALESCE(t.n, 0) < r.min_n
    THEN 'te_weinig_data'
    ELSE 'meetwaarde'
  END AS weergave,
  (
    r.bouwstatus <> 'gepland_2027'
  ) AS tonen_op_dashboard,
  CASE
    WHEN r.bouwstatus = 'gepland_2027'
    THEN 'In te vullen vanaf 2027'
    WHEN r.bouwstatus = 'tbd'
    THEN 'Definitie nog niet vastgesteld'
    WHEN r.bouwstatus = 'in_ontwikkeling'
    THEN 'Nog in opbouw'
    WHEN COALESCE(bs.niveau, ba.niveau) = 'onbetrouwbaar'
    THEN COALESCE(bs.reden, ba.reden)
    WHEN r.bouwstatus = 'handmatig' AND t.waarde IS NULL
    THEN 'Wacht op invoer door ' || r.eigenaar
    WHEN t.leeg_reden IS NULL AND COALESCE(t.n, 0) < r.min_n
    THEN 'Te weinig waarnemingen: ' || COALESCE(t.n, 0) || ' van minimaal ' || r.min_n
    ELSE t.leeg_reden
  END AS leeg_reden,
  CASE WHEN d.doel IS NULL THEN 'geen doel ingesteld' END AS doel_tekst,
  COALESCE(t.venster_tekst, r.venster) AS venster,
  r.updatefrequentie,
  r.historie_view,
  t.stand_per,
  t.bron_bijgewerkt,
  r.definitie,
  r.definitie_versie,
  r.definitie_geldig_vanaf,
  r.wijziging,
  t.toelichting,
  r.kanttekening,
  r.aanname,
  COALESCE(bs.niveau, ba.niveau) AS betrouwbaarheid,
  COALESCE(bs.reden, ba.reden) AS betrouwbaarheid_reden
FROM "My Queries".kpi_registry AS r
LEFT JOIN tegels_actueel AS t
  ON t.kpi_code = r.kpi_code
LEFT JOIN doel_actueel AS d
  ON d.kpi_code = t.kpi_code AND d.scope_code = t.scope_code
LEFT JOIN betr AS bs
  ON bs.kpi_code = r.kpi_code AND bs.scope_code = t.scope_code
LEFT JOIN betr AS ba
  ON ba.kpi_code = r.kpi_code AND ba.scope_code IS NULL
LEFT JOIN eigenaar_scope AS es
  ON es.kpi_code = r.kpi_code AND es.scope_code = t.scope_code
