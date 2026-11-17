-- Peliqan "My Queries".afc_klant_live_my_queries (table_id 1586649), databaseview, aangemaakt 2026-11-16
-- AFC-analyse (awc-dashboard) | LIVE kopie van afc_control_center.afc_klant (Floor), 16-11-2026.
-- Zelfde SQL als Floor, maar als databaseview op "My Queries".afc_zending_live_my_queries (live) in plaats van de dagelijkse snapshot.
-- Wijzigt Floor zijn afc_klant, neem dat hier over. Contract: documentation/AFC-analyse.md.
-- Klantgroep: vaste debiteur van de klant (debiteur met de meeste gefactureerde omzet), behalve als die debiteur
--   voor derden betaalt (AWC 010812, Peeters 010931, Sim Cargo 100170, ParQ 100583, Loogman 111583, Jaspers 398210).
-- Status (besluit Floor 11-11-2026): Verloren = laatste zending > 90 dagen geleden (Eenmalig bij 1 zending);
--   Nieuw = eerste zending < 365 dagen geleden; Dalend = omzet laatste 12 mnd < 75% van de 12 mnd daarvoor; anders Actief.
with z as (
  select * from "My Queries".afc_zending_live_my_queries where not geannuleerd and klant_id is not null
),
derden as (
  select unnest(array['010812', '010931', '100170', '100583', '111583', '398210']) as debiteurnummer
),
kd as (
  select klant_id, debiteurnummer,
         row_number() over (partition by klant_id order by sum(coalesce(omzet_cash, 0) + coalesce(invoerrechten_cash, 0)) desc, count(*) desc) as rn
  from z
  where debiteurnummer is not null and debiteurnummer not in (select debiteurnummer from derden)
  group by 1, 2
),
a as (
  select
    klant_id,
    max(klant) as klant,
    min(aanmaakdatum) as eerste_zending,
    max(aanmaakdatum) as laatste_zending,
    count(*) as zendingen_totaal,
    sum(case when aanmaakdatum > current_date - 365 then 1 else 0 end) as zendingen_12m,
    sum(case when aanmaakdatum > current_date - 365 then omzet_sprinter else 0 end) as omzet_12m,
    sum(case when aanmaakdatum > current_date - 365 then marge_sprinter else 0 end) as marge_12m,
    sum(case when aanmaakdatum <= current_date - 365 and aanmaakdatum > current_date - 730 then omzet_sprinter else 0 end) as omzet_vorige_12m,
    sum(case when aanmaakdatum <= current_date - 365 and aanmaakdatum > current_date - 730 then marge_sprinter else 0 end) as marge_vorige_12m,
    string_agg(distinct case when aanmaakdatum > current_date - 365 then modaliteit end, ', ') as modaliteiten_12m,
    string_agg(distinct case when aanmaakdatum <= current_date - 365 and aanmaakdatum > current_date - 730 then modaliteit end, ', ') as modaliteiten_vorige_12m,
    string_agg(distinct case when extract(year from aanmaakdatum) = extract(year from current_date) then modaliteit end, ', ') as modaliteiten_dit_jaar,
    string_agg(distinct case when extract(year from aanmaakdatum) = extract(year from current_date) - 1 then modaliteit end, ', ') as modaliteiten_vorig_jaar,
    sum(case when extract(year from aanmaakdatum) = extract(year from current_date) then omzet_sprinter else 0 end) as omzet_dit_jaar,
    sum(case when extract(year from aanmaakdatum) = extract(year from current_date) - 1 then omzet_sprinter else 0 end) as omzet_vorig_jaar,
    string_agg(distinct eigenaar, ', ') filter (where aanmaakdatum > current_date - 365) as eigenaren_12m
  from z
  group by 1
)
select
  a.klant_id,
  a.klant,
  kd.debiteurnummer as vaste_debiteur,
  coalesce(kd.debiteurnummer, 'S' || a.klant_id) as klantgroep_id,
  a.eerste_zending,
  cast(date_trunc('month', a.eerste_zending) as date) as eerste_zending_maand,
  a.laatste_zending,
  current_date - a.laatste_zending as dagen_sinds_laatste_zending,
  a.zendingen_totaal,
  a.zendingen_12m,
  round(a.omzet_12m, 2) as omzet_12m,
  round(a.marge_12m, 2) as marge_12m,
  round(a.omzet_vorige_12m, 2) as omzet_vorige_12m,
  round(a.marge_vorige_12m, 2) as marge_vorige_12m,
  round(a.omzet_dit_jaar, 2) as omzet_dit_jaar,
  round(a.omzet_vorig_jaar, 2) as omzet_vorig_jaar,
  a.modaliteiten_vorig_jaar,
  a.modaliteiten_dit_jaar,
  a.modaliteiten_vorige_12m,
  a.modaliteiten_12m,
  (a.modaliteiten_vorig_jaar is not null and a.modaliteiten_dit_jaar is not null
     and exists (select 1 from unnest(string_to_array(a.modaliteiten_dit_jaar, ', ')) m
                 where m not in (select unnest(string_to_array(a.modaliteiten_vorig_jaar, ', '))))) as nieuwe_dienst_dit_jaar,
  case
    when a.laatste_zending <= current_date - 90 and a.zendingen_totaal = 1 then 'Eenmalig'
    when a.laatste_zending <= current_date - 90 then 'Verloren'
    when a.eerste_zending > current_date - 365 then 'Nieuw'
    when a.omzet_vorige_12m > 0 and a.omzet_12m < 0.75 * a.omzet_vorige_12m then 'Dalend'
    else 'Actief'
  end as klantstatus,
  a.eigenaren_12m
from a
left join kd on kd.klant_id = a.klant_id and kd.rn = 1
