-- Peliqan "My Queries".kpi_winrate_fases (table_id 1416339), stand 2026-11-12
-- Mapping fase -> uitkomst, gesleuteld op HubSpot pipeline_id + stage_id (robuust tegen hernoemen).
-- pipeline = vaste scope_code van het dashboard; fase = leesbaar label (niet gebruikt voor de join).
SELECT
  *
FROM (VALUES
  ('Verkooppijplijn', 'Eerste levering', 'gewonnen', 'HubSpot-vlag gewonnen', 'default', 'closedwon'),
  ('Verkooppijplijn', 'Opdracht', 'gewonnen', 'Bevestigd 21 sep 2026: Opdracht betekent gewonnen. Sinds nov 2025 gaan deals niet meer door naar Eerste levering.', 'default', 'contractsent'),
  ('Verkooppijplijn', 'Sluiting verloren', 'verloren', 'HubSpot-vlag verloren', 'default', 'closedlost'),
  ('AFC - Verkooplijn', 'Gewonnen', 'gewonnen', 'HubSpot-vlag gewonnen (fase heette tot 4 nov 2026 Closed Won)', '122426814', '2151166173'),
  ('AFC - Verkooplijn', 'Verloren', 'verloren', 'HubSpot-vlag verloren (fase heette tot 3 nov 2026 Closed Lost)', '122426814', '2151166174')) AS v(pipeline, fase, uitkomst, bron, pipeline_id, stage_id)
