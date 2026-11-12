-- Peliqan "My Queries".kpi_winrate_basis (table_id 1416340), stand 2026-11-12
-- Winrate-basis, id-gebaseerd (2026-11-12): pipeline en fase -> uitkomst via HubSpot-ids, niet via labels.
-- scope: vaste mapping pipeline_id -> scope_code die het dashboard verwacht (los van de huidige HubSpot-naam).
-- st: deals_pipeline__stages bevat soms meerdere rijen per stage (oude + nieuwe label); neem per (pipeline, stage) alleen de laatste.
WITH scope AS (
  SELECT * FROM (VALUES
    ('default', 'Verkooppijplijn'),
    ('122426814', 'AFC - Verkooplijn')) AS v(pipeline_id, scope_code)
),
st AS (
  SELECT id, _sdc_source_key_id AS pipeline_id, label,
    ROW_NUMBER() OVER (PARTITION BY _sdc_source_key_id, id ORDER BY _sdc_sequence DESC, updatedat DESC NULLS LAST, _sdc_level_0_id DESC) AS rn
  FROM hubspot_v2.deals_pipeline__stages
)
SELECT d.id AS deal_id,
  sc.scope_code AS pipeline,
  s.label AS fase,
  f.uitkomst,
  d.createdate,
  CASE WHEN f.uitkomst IS NOT NULL THEN d.hs_v2_date_entered_current_stage END AS beslisdatum,
  (d.hs_is_closed_won = 'true') AS hubspot_vlag_gewonnen,
  d._sdc_batched_at
FROM hubspot_v2.deals d
JOIN scope sc ON sc.pipeline_id = TRIM(d.pipeline)
LEFT JOIN st s ON s.id = TRIM(d.dealstage) AND s.pipeline_id = sc.pipeline_id AND s.rn = 1
LEFT JOIN "My Queries".kpi_winrate_fases f ON f.pipeline_id = sc.pipeline_id AND f.stage_id = TRIM(d.dealstage)
WHERE COALESCE(d.archived, false) = false
