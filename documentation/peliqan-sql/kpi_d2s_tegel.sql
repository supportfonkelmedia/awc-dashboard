-- Peliqan "My Queries".kpi_d2s_tegel (table_id 1416770), stand 2026-11-12
WITH m AS (
  SELECT *, LAG(pct_binnen_24u) OVER (ORDER BY maand) AS vorige,
    ROW_NUMBER() OVER (ORDER BY maand DESC) AS rn
  FROM kpi_data.dock_to_stock_maand
  WHERE maand < CAST(DATE_TRUNC('month', CURRENT_DATE) AS date)
)
SELECT 'dock_to_stock' AS kpi_code, 'alaw' AS scope_code, 'AWC' AS scope_label,
  m.pct_binnen_24u AS waarde, m.vorige AS waarde_vorige, ROUND(m.pct_binnen_24u - m.vorige, 1) AS delta,
  CAST(m.met_verplaatsing AS bigint) AS n, CAST(NULL AS text) AS leeg_reden,
  'Inbounds gelost in ' || TO_CHAR(m.maand, 'MM-YYYY') || ', alleen afgelopen maanden' AS venster,
  m.maand AS stand_per, m.geschreven_op AS bron_bijgewerkt,
  m.binnen_24u || ' van ' || m.met_verplaatsing || ' inbounds binnen 24 uur in de stelling. '
    || ROUND(100 - m.pct_met_verplaatsing, 1) || '% van de ' || m.inbounds || ' inbounds heeft geen verplaatsing en telt niet mee.' AS toelichting
FROM m
WHERE m.rn = 1
