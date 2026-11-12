-- Peliqan "My Queries".kpi_triple_lob_tegel (table_id 1416461), stand 2026-11-12
WITH m AS (
  SELECT *, LAG(pct_klanten_zeker) OVER (ORDER BY maand) AS vorige,
    ROW_NUMBER() OVER (ORDER BY maand DESC) AS rn
  FROM "My Queries".kpi_triple_lob_maand
),
s AS (SELECT MAX(_sdc_batched_at) AS ts FROM cashweb.ledger_mutations WHERE admin_code IN ('alaw','pgl1','acco'))
SELECT 'triple_lob' AS kpi_code, 'concern' AS scope_code, 'Concern (AWC, AFC, ACC)' AS scope_label,
  m.pct_klanten_zeker AS waarde, m.vorige AS waarde_vorige, ROUND(m.pct_klanten_zeker - m.vorige, 1) AS delta,
  CAST(m.klanten AS bigint) AS n, CAST(NULL AS text) AS leeg_reden,
  'Twaalf maanden t/m ' || TO_CHAR(m.maand, 'MM-YYYY') || ', alleen afgesloten maanden' AS venster,
  m.maand AS stand_per, s.ts AS bron_bijgewerkt,
  m.triple_zeker || ' van ' || m.klanten || ' klanten zeker in alle drie; met zelfde concern ' || m.pct_klanten_met_concern
    || '%. Omzetaandeel ' || m.pct_omzet_zeker || '%.'
    || CASE WHEN m.triple_te_controleren > 0 THEN ' ' || m.triple_te_controleren || ' nieuwe match(es) nog te controleren.' ELSE '' END AS toelichting
FROM m, s
WHERE m.rn = 1
