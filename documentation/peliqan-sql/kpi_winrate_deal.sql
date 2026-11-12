-- Peliqan "My Queries".kpi_winrate_deal_my_queries (DB-view, aangemaakt 2026-11-12)
-- Drill onder de Winrate-tegels: welke deals tellen mee, gewonnen of verloren, en op welke dag beslist.
-- Zelfde logica als kpi_winrate_basis + kpi_winrate_maand (soort 'vandaag'): deals aangemaakt in de
-- 12 maanden voor vandaag; tellen mee als de fase een uitkomst heeft (kpi_winrate_fases, op HubSpot-ids)
-- en de beslisdatum voor vandaag ligt. Inline i.p.v. via kpi_winrate_basis omdat een DB-view alleen
-- echte tabellen/views kan lezen; de fasemapping komt uit de replica kpi_winrate_fases_my_queries.
-- bulkdag = 10 of meer beslissingen op dezelfde dag in dezelfde pijplijn (bijv. opschoning 21 aug 2026).
WITH scope AS (
  SELECT * FROM (VALUES
    ('default', 'Verkooppijplijn'),
    ('122426814', 'AFC - Verkooplijn')) AS v(pipeline_id, scope_code)
),
st AS (
  SELECT id, _sdc_source_key_id AS pipeline_id, label,
    ROW_NUMBER() OVER (PARTITION BY _sdc_source_key_id, id ORDER BY _sdc_sequence DESC, updatedat DESC NULLS LAST, _sdc_level_0_id DESC) AS rn
  FROM hubspot_v2.deals_pipeline__stages
),
o AS (
  SELECT DISTINCT ON (id) id, NULLIF(TRIM(COALESCE(firstname, '') || ' ' || COALESCE(lastname, '')), '') AS naam
  FROM hubspot_v2.owners
  ORDER BY id, _sdc_sequence DESC NULLS LAST
),
b AS (
  SELECT d.id AS deal_id,
    sc.scope_code,
    NULLIF(TRIM(d.dealname), '') AS deal,
    s.label AS fase,
    f.uitkomst,
    d.createdate,
    CASE WHEN f.uitkomst IS NOT NULL THEN d.hs_v2_date_entered_current_stage END AS beslis_ts,
    CAST(NULLIF(CAST(d.amount AS text), '') AS numeric) AS bedrag,
    TRIM(d.hubspot_owner_id) AS owner_id
  FROM hubspot_v2.deals d
  JOIN scope sc ON sc.pipeline_id = TRIM(d.pipeline)
  LEFT JOIN st s ON s.id = TRIM(d.dealstage) AND s.pipeline_id = sc.pipeline_id AND s.rn = 1
  LEFT JOIN "My Queries".kpi_winrate_fases_my_queries f ON f.pipeline_id = sc.pipeline_id AND f.stage_id = TRIM(d.dealstage)
  WHERE COALESCE(d.archived, false) = false
    AND d.createdate >= CURRENT_DATE - INTERVAL '24 months'
),
bd AS (
  SELECT b.*,
    CASE WHEN beslis_ts IS NOT NULL
      THEN COUNT(*) OVER (PARTITION BY scope_code, CAST(beslis_ts AS date)) END AS beslissingen_die_dag
  FROM b
)
SELECT
  bd.scope_code,
  CASE
    WHEN bd.createdate >= CURRENT_DATE - INTERVAL '12 months' AND bd.createdate < CURRENT_DATE
      THEN CASE WHEN bd.uitkomst IS NOT NULL AND bd.beslis_ts < CURRENT_DATE THEN 'telt mee' ELSE 'nog open' END
    ELSE 'buiten venster'
  END AS tegelvenster,
  COALESCE(bd.deal, '(geen naam) ' || bd.deal_id) AS deal,
  bd.fase,
  bd.uitkomst,
  CAST(bd.createdate AS date) AS aangemaakt,
  CAST(bd.beslis_ts AS date) AS beslisdatum,
  bd.beslissingen_die_dag,
  COALESCE(bd.beslissingen_die_dag >= 10, false) AS bulkdag,
  bd.bedrag,
  o.naam AS eigenaar,
  bd.deal_id
FROM bd
LEFT JOIN o ON o.id = bd.owner_id
