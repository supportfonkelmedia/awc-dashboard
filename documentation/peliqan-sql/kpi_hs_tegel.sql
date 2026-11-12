-- Peliqan "My Queries".kpi_hs_tegel (table_id 1416440), stand 2026-11-12 na jaarwisselingsfix: in januari het hele vorige jaar (CTE p) in plaats van een leeg nieuw jaar. Vorige versie: commit 66cd6a6.
WITH tk AS (
  SELECT TRIM(hs_pipeline) AS pijplijn, TRIM(hs_pipeline_stage) AS fase, createdate, type_aanvraag, _sdc_batched_at,
    CASE WHEN TRIM(hs_pipeline)='1283749104' THEN COALESCE(closed_date, CAST(NULLIF(hs_date_entered_1754175726,'') AS timestamptz))
         ELSE COALESCE(CAST(NULLIF(hs_date_entered_248014792,'') AS timestamptz), closed_date) END AS eind_ts
  FROM hubspot_v2.tickets
  WHERE COALESCE(archived,false)=false AND TRIM(hs_pipeline) IN ('1283749104','121633735')
),
sync_t AS (SELECT MAX(_sdc_batched_at) AS ts FROM tk),
p AS (
  SELECT CAST(DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 month') AS timestamptz) AS van,
    LEAST(NOW(), CAST(DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 month') + INTERVAL '1 year' AS timestamptz)) AS tot,
    CAST(EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 month') AS int) AS jaar
),
dos AS (
  SELECT COUNT(*) AS n,
    SUM(CASE WHEN type_aanvraag='Import' THEN 1 ELSE 0 END) AS imp,
    SUM(CASE WHEN type_aanvraag='Export' THEN 1 ELSE 0 END) AS exp,
    SUM(CASE WHEN type_aanvraag='Consult' THEN 1 ELSE 0 END) AS con
  FROM tk, p WHERE pijplijn='1283749104' AND createdate >= p.van AND createdate <= p.tot
),
dlt AS (
  SELECT COUNT(*) AS n, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (eind_ts - createdate))/86400) AS med
  FROM tk, p WHERE pijplijn='1283749104' AND fase='1754175726' AND eind_ts >= p.van AND eind_ts <= p.tot AND eind_ts >= createdate
),
onb AS (
  SELECT COUNT(*) AS n, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (eind_ts - createdate))/86400) AS med
  FROM tk, p WHERE pijplijn='121633735' AND fase='248014792' AND eind_ts >= p.van AND eind_ts <= p.tot AND eind_ts >= createdate
),
co AS (
  SELECT CAST(NULLIF(hs_v2_date_exited_customer,'') AS timestamptz) AS vt, _sdc_batched_at
  FROM hubspot_v2.companies WHERE COALESCE(archived,false)=false AND NULLIF(hs_v2_date_exited_customer,'') IS NOT NULL
),
co_d AS (SELECT vt, COUNT(*) OVER (PARTITION BY DATE(vt)) AS per_dag FROM co WHERE vt <= NOW()),
chu AS (
  SELECT
    SUM(CASE WHEN vt > NOW() - INTERVAL '12 months' THEN 1 ELSE 0 END) AS nu,
    SUM(CASE WHEN vt > NOW() - INTERVAL '24 months' AND vt <= NOW() - INTERVAL '12 months' THEN 1 ELSE 0 END) AS vorig,
    SUM(CASE WHEN vt > NOW() - INTERVAL '12 months' AND per_dag >= 10 THEN 1 ELSE 0 END) AS bulk
  FROM co_d
),
sync_c AS (SELECT MAX(_sdc_batched_at) AS ts FROM co)
SELECT 'churn' AS kpi_code, 'concern' AS scope_code, 'Concern' AS scope_label,
  CAST(chu.nu AS numeric) AS waarde, CAST(chu.vorig AS numeric) AS waarde_vorige, CAST(chu.nu - chu.vorig AS numeric) AS delta,
  CAST(chu.nu AS bigint) AS n, CAST(NULL AS text) AS leeg_reden,
  'Afgelopen 12 maanden, tegenover de 12 daarvoor' AS venster, CURRENT_DATE AS stand_per, sync_c.ts AS bron_bijgewerkt,
  chu.bulk || ' van de ' || chu.nu || ' vertrekken vallen op dagen met 10 of meer tegelijk (bulkcorrecties).' AS toelichting
FROM chu, sync_c
UNION ALL
SELECT 'acc_dossiers', 'acco', 'ACC', CAST(dos.n AS numeric), CAST(NULL AS numeric), CAST(NULL AS numeric), CAST(dos.n AS bigint), CAST(NULL AS text),
  CASE WHEN p.tot < NOW() THEN 'Kalenderjaar ' || p.jaar ELSE 'Kalenderjaar tot nu' END, CURRENT_DATE, sync_t.ts,
  'Import ' || dos.imp || ' · Export ' || dos.exp || ' · Consult ' || dos.con || ' · Overig ' || (dos.n - dos.imp - dos.exp - dos.con)
FROM dos, sync_t, p
UNION ALL
SELECT 'acc_doorlooptijd', 'acco', 'ACC', ROUND(CAST(dlt.med AS numeric),1), CAST(NULL AS numeric), CAST(NULL AS numeric), CAST(dlt.n AS bigint), CAST(NULL AS text),
  CASE WHEN p.tot < NOW() THEN 'Dossiers afgerond in ' || p.jaar ELSE 'Dossiers afgerond in het kalenderjaar tot nu' END, CURRENT_DATE, sync_t.ts, 'Mediaan in dagen, van aanmaken tot verwerkt.'
FROM dlt, sync_t, p
UNION ALL
SELECT 'time_to_onboarding', 'alaw', 'AWC', ROUND(CAST(onb.med AS numeric),1), CAST(NULL AS numeric), CAST(NULL AS numeric), CAST(onb.n AS bigint), CAST(NULL AS text),
  CASE WHEN p.tot < NOW() THEN 'Onboardings afgerond in ' || p.jaar ELSE 'Onboardings afgerond in het kalenderjaar tot nu' END, CURRENT_DATE, sync_t.ts, 'Mediaan in dagen, van aanmaken van het ticket tot Onboard.'
FROM onb, sync_t, p

