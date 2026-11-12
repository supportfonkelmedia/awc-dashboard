-- Peliqan "My Queries".kpi_afc_klant_retentie_jaar_my_queries (table_id 1579284), stand 2026-11-12
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | klantbehoud per kalenderjaar (aanmaakdatum) t.o.v. het jaar ervoor
-- Klant = Sprinter-opdrachtgever (klant_id). Omzet excl. invoerrechten. Data begint maart 2023.
-- Bron: afc_control_center.afc_zending (Floor). Contract: documentation/AFC-analyse.md in awc-dashboard.
with z as (
  select klant_id, extract(year from aanmaakdatum)::int as jaar, count(*) as n,
         sum(coalesce(omzet_sprinter, 0) - coalesce(invoerrechten_cash, 0)) as omzet
  from afc_control_center.afc_zending_afc_control_center
  where not geannuleerd and klant_id is not null and aanmaakdatum <= current_date
  group by 1, 2
),
f as (select klant_id, min(jaar) as eerste_jaar from z group by 1),
j as (select distinct jaar from z),
c as (
  select j.jaar,
    count(distinct cur.klant_id) as actieve_klanten,
    count(distinct case when cur.klant_id is not null and prev.klant_id is not null then cur.klant_id end) as behouden,
    count(distinct case when prev.klant_id is not null and cur.klant_id is null then prev.klant_id end) as weggevallen,
    count(distinct case when cur.klant_id is not null and f.eerste_jaar = j.jaar then cur.klant_id end) as nieuw,
    count(distinct case when cur.klant_id is not null and prev.klant_id is null and f.eerste_jaar < j.jaar then cur.klant_id end) as teruggekeerd,
    count(distinct case when cur.n = 1 then cur.klant_id end) as met_1_zending,
    count(distinct prev.klant_id) as actief_vorig_jaar,
    round(sum(case when prev.klant_id is not null and cur.klant_id is null then prev.omzet else 0 end), 2) as omzet_weggevallen_vorig_jaar,
    round(sum(case when cur.klant_id is not null and f.eerste_jaar = j.jaar then cur.omzet else 0 end), 2) as omzet_nieuwe_klanten
  from j
  cross join (select distinct klant_id from z) k
  left join z cur on cur.klant_id = k.klant_id and cur.jaar = j.jaar
  left join z prev on prev.klant_id = k.klant_id and prev.jaar = j.jaar - 1
  left join f on f.klant_id = k.klant_id
  group by 1
)
select *,
  round(100.0 * behouden / nullif(actief_vorig_jaar, 0), 1) as retentie_pct,
  round(100.0 * weggevallen / nullif(actief_vorig_jaar, 0), 1) as churn_pct,
  (jaar = extract(year from current_date)::int) as lopend_jaar
from c
