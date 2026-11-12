-- Peliqan "My Queries".kpi_afc_offerte_maand_my_queries (table_id 1579304), databaseview, aangemaakt 2026-11-12
-- Zie de SQL-commentaarregels in Peliqan; definitie: gewonnen / (gewonnen + afgewezen + verlopen), venster 12 maanden.
with o as (
  select cast(date_trunc('month', aanmaakdatum) as date) as maand, status_afgeleid as s
  from afc_control_center.afc_offerte_afc_control_center
),
m as (
  select cast(g as date) as maand
  from generate_series(date '2024-01-01', cast(date_trunc('month', current_date) as date), interval '1 month') as g
),
r as (
  select m.maand,
    sum(case when o.s = 'Gewonnen' then 1 else 0 end) as gewonnen,
    sum(case when o.s = 'Afgewezen' then 1 else 0 end) as afgewezen,
    sum(case when o.s = 'Verlopen' then 1 else 0 end) as verlopen,
    sum(case when o.s like 'Open%' then 1 else 0 end) as nog_open,
    sum(case when o.maand = m.maand then 1 else 0 end) as aangemaakt_in_maand
  from m left join o on o.maand > m.maand - interval '12 month' and o.maand <= m.maand
  group by 1
)
select maand, gewonnen, afgewezen, verlopen, nog_open,
  gewonnen + afgewezen + verlopen as beslist,
  round(100.0 * gewonnen / nullif(gewonnen + afgewezen + verlopen, 0), 1) as conversie_pct,
  aangemaakt_in_maand,
  case when maand >= cast(date_trunc('month', current_date) as date) then 'voorlopig' else 'volledig' end as status
from r
