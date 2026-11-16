-- Peliqan "My Queries".afc_zending_live_my_queries (table_id 1586647), databaseview, aangemaakt 2026-11-16
-- AFC-analyse (awc-dashboard) | LIVE kopie van afc_control_center.afc_zending (Floor), 16-11-2026.
-- Zelfde SQL als Floor, maar als databaseview: leest sprinter_api.shipments rechtstreeks, zonder dagelijkse snapshot.
-- sprinter_api.shipments wordt live bijgewerkt door de KPI-handler (app 17395) bij elke opvraag van de AFC-analyse
-- (nieuwste zendingen uit de Sprinter-API, max. 1x per minuut) en 's nachts diep door app 18062.
-- Cash-facturatie (afc_omzetregel) blijft de dagelijkse snapshot van Floor: Cash zelf ververst ook dagelijks.
-- Wijzigt Floor zijn afc_zending, neem dat hier over. Contract: documentation/AFC-analyse.md.
with o as (
  select zendingnummer,
    sum(case when soort = 'omzet' then bedrag_excl_btw else 0 end) as omzet_cash,
    sum(case when soort = 'invoerrechten' then bedrag_excl_btw else 0 end) as invoerrechten_cash,
    sum(btw_naar_rato) as btw_cash,
    min(factuurdatum) as eerste_factuurdatum,
    max(factuurdatum) as laatste_factuurdatum,
    count(distinct document) as aantal_facturen
  from afc_control_center.afc_omzetregel_afc_control_center
  where zendingnummer is not null
  group by 1
),
od as (
  select zendingnummer, debiteurnummer,
         row_number() over (partition by zendingnummer order by sum(bedrag_excl_btw) desc) as rn
  from afc_control_center.afc_omzetregel_afc_control_center
  where zendingnummer is not null and debiteurnummer is not null
  group by 1, 2
),
rel as (
  select relation_number, max(name) as name from cashweb.relation where admin_code = 'pgl1' group by 1
)
select
  s.shipment_number as zendingnummer,
  s.shipment_id,
  s.customer_company_id as klant_id,
  c.name as klant,
  od.debiteurnummer,
  rel.name as debiteur_naam,
  case s.shipment_mode when 'R' then 'Road' when 'S' then 'Sea' when 'A' then 'Air' else s.shipment_mode end as modaliteit,
  case s.direction when 'E' then 'Export' when 'I' then 'Import' when 'D' then 'Domestic' else s.direction end as richting,
  coalesce(nullif(s.department, ''), '(geen)') as afdeling,
  s.shipment_owner as eigenaar,
  s.shipment_status_code as status_code,
  case s.shipment_status_code when 'O' then 'Operational' when 'I' then 'Invoiced' when 'C' then 'Cancelled' else 'Onbekend (' || coalesce(s.shipment_status_code, '') || ')' end as status,
  s.shipment_status as record_status,
  case s.shipment_status when 15 then 'Actief' when 16 then 'Gearchiveerd' else 'Overig (' || s.shipment_status || ')' end as record_status_naam,
  (s.shipment_status_code = 'C') as geannuleerd,
  cast(s.create_date as date) as aanmaakdatum,
  cast(s.report_date as date) as rapportagedatum,
  cast(date_trunc('month', s.report_date) as date) as rapportagemaand,
  extract(year from s.report_date)::int as rapportagejaar,
  (extract(month from s.report_date) = 1 and extract(day from s.report_date) = 1
     and extract(year from s.create_date) < extract(year from s.report_date)) as rapportagedatum_jaarovergang,
  round(cast(s.total_sales_amount as numeric), 2) as omzet_sprinter,
  round(cast(s.total_purchase_amount as numeric), 2) as inkoop_sprinter,
  round(cast(s.total_gpm_amount as numeric), 2) as marge_sprinter,
  case when s.total_sales_amount <> 0 then round(cast(100 * s.total_gpm_amount / s.total_sales_amount as numeric), 1) end as marge_pct,
  round(o.omzet_cash, 2) as omzet_cash,
  round(o.invoerrechten_cash, 2) as invoerrechten_cash,
  round(o.btw_cash, 2) as btw_cash,
  (o.zendingnummer is not null) as gefactureerd_cash,
  o.eerste_factuurdatum,
  o.laatste_factuurdatum,
  coalesce(o.aantal_facturen, 0) as aantal_facturen,
  s.quotation_id as offerte_id,
  s.incoterms,
  s.external_reference as klantreferentie,
  s.total_gross_weight as gewicht_kg,
  s.total_volume as volume_m3,
  s.total_loading_meter as laadmeter,
  s.update_date as laatst_gewijzigd_sprinter
from sprinter_api.shipments s
left join sprinter_api.companies c on c.company_id = s.customer_company_id
left join o on o.zendingnummer = s.shipment_number
left join od on od.zendingnummer = s.shipment_number and od.rn = 1
left join rel on rel.relation_number = od.debiteurnummer
