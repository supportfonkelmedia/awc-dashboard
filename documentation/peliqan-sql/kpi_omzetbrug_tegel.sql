-- Peliqan "My Queries".kpi_omzetbrug_tegel (table_id 1416721), stand 2026-11-12
WITH b AS (
  SELECT CASE scope WHEN 'Concern' THEN 'concern' WHEN 'AWC' THEN 'alaw' WHEN 'AFC' THEN 'pgl1' ELSE 'acco' END AS scope_code,
    CASE scope WHEN 'Concern' THEN 'Concern (AWC, AFC, ACC)' ELSE scope END AS scope_label,
    MAX(stand_per) AS stand_per,
    SUM(bedrag) FILTER (WHERE component='start') AS start_bedrag,
    SUM(bedrag) FILTER (WHERE component='eind') AS eind_bedrag,
    SUM(klanten) FILTER (WHERE component='eind') AS eind_klanten,
    SUM(bedrag) FILTER (WHERE component='nieuw') AS nieuw, SUM(klanten) FILTER (WHERE component='nieuw') AS n_nieuw,
    SUM(bedrag) FILTER (WHERE component='gegroeid') AS gegroeid, SUM(klanten) FILTER (WHERE component='gegroeid') AS n_gegroeid,
    SUM(bedrag) FILTER (WHERE component='gekrompen') AS gekrompen, SUM(klanten) FILTER (WHERE component='gekrompen') AS n_gekrompen,
    SUM(bedrag) FILTER (WHERE component='verloren') AS verloren, SUM(klanten) FILTER (WHERE component='verloren') AS n_verloren
  FROM "My Queries".kpi_omzetbrug GROUP BY 1,2
),
s AS (SELECT MAX(_sdc_batched_at) AS ts FROM cashweb.ledger_mutations WHERE admin_code IN ('alaw','pgl1','acco'))
SELECT 'omzet_brug' AS kpi_code, b.scope_code, b.scope_label,
  b.eind_bedrag AS waarde, b.start_bedrag AS waarde_vorige, b.eind_bedrag - b.start_bedrag AS delta,
  CAST(b.eind_klanten AS bigint) AS n, CAST(NULL AS text) AS leeg_reden,
  'Twaalf maanden t/m ' || TO_CHAR(b.stand_per, 'MM-YYYY') || ' tegenover de twaalf daarvoor' AS venster,
  b.stand_per, s.ts AS bron_bijgewerkt,
  'Groei ' || ROUND(100.0 * (b.eind_bedrag - b.start_bedrag) / NULLIF(b.start_bedrag,0), 1) || '%. Nieuw ' || b.n_nieuw || ' klanten (' || ROUND(b.nieuw/1000) || 'K), gegroeid '
    || b.n_gegroeid || ' (' || ROUND(b.gegroeid/1000) || 'K), gekrompen ' || b.n_gekrompen || ' (' || ROUND(b.gekrompen/1000) || 'K), verloren '
    || b.n_verloren || ' (' || ROUND(b.verloren/1000) || 'K).' AS toelichting
FROM b, s
