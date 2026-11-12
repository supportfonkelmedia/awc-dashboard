-- Peliqan "My Queries".kpi_churn_klant_my_queries (DB-view, aangemaakt 2026-11-12)
-- Drill onder de Churn-tegel: welke klanten vertrokken, op welke dag, en of dat een bulkdag was.
-- Zelfde definitie als kpi_hs_tegel (churn): bedrijven met hs_v2_date_exited_customer, niet gearchiveerd,
-- vertrekdatum <= nu; bulkdag = 10 of meer vertrekken op dezelfde dag (geteld over vertrekken t/m nu).
-- tegelvenster volgt de tegel: 'laatste 12 maanden' = waarde, '12 maanden daarvoor' = waarde_vorige.
WITH c AS (
  SELECT
    id AS company_id,
    NULLIF(TRIM(name), '') AS klant,
    CAST(NULLIF(hs_v2_date_exited_customer, '') AS TIMESTAMPTZ) AS vertrek_ts,
    lifecyclestage,
    (CASE WHEN icp__euhubbehoefte = 'Yes' THEN 1 ELSE 0 END
      + CASE WHEN icp__meerjarige_samenwerking = 'Yes' THEN 1 ELSE 0 END
      + CASE WHEN icp__noneu_naar_eu_stromen = 'Yes' THEN 1 ELSE 0 END
      + CASE WHEN icp__premium__compliance_mindset = 'Yes' THEN 1 ELSE 0 END
      + CASE WHEN icp__producent__brand_owner = 'Yes' THEN 1 ELSE 0 END) AS icp_ja,
    (NULLIF(icp__euhubbehoefte, '') IS NOT NULL
      OR NULLIF(icp__meerjarige_samenwerking, '') IS NOT NULL
      OR NULLIF(icp__noneu_naar_eu_stromen, '') IS NOT NULL
      OR NULLIF(icp__premium__compliance_mindset, '') IS NOT NULL
      OR NULLIF(icp__producent__brand_owner, '') IS NOT NULL) AS gescoord
  FROM hubspot_v2.companies
  WHERE COALESCE(archived, FALSE) = FALSE
    AND NULLIF(hs_v2_date_exited_customer, '') IS NOT NULL
),
d AS (
  SELECT c.*, COUNT(*) OVER (PARTITION BY DATE(vertrek_ts)) AS vertrekken_die_dag
  FROM c
  WHERE vertrek_ts <= NOW()
)
SELECT
  'concern' AS scope_code,
  CASE
    WHEN d.vertrek_ts > NOW() - INTERVAL '12 months' THEN 'laatste 12 maanden'
    WHEN d.vertrek_ts > NOW() - INTERVAL '24 months' THEN '12 maanden daarvoor'
    ELSE 'ouder'
  END AS tegelvenster,
  CAST(d.vertrek_ts AS DATE) AS vertrekdatum,
  'Q' || EXTRACT(QUARTER FROM d.vertrek_ts) || ' ' || EXTRACT(YEAR FROM d.vertrek_ts) AS kwartaal,
  COALESCE(d.klant, '(geen naam) ' || d.company_id) AS klant,
  d.vertrekken_die_dag,
  (d.vertrekken_die_dag >= 10) AS bulkdag,
  CASE WHEN d.gescoord THEN d.icp_ja END AS icp_score,
  (d.lifecyclestage = 'customer') AS nu_weer_klant,
  d.company_id
FROM d
