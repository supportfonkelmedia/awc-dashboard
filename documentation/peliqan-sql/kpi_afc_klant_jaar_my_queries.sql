-- Peliqan "My Queries".kpi_afc_klant_jaar_my_queries (table_id 1579282), stand 2026-11-12
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | klantgroep x jaar x richting x modaliteit x ytd_venster, lopend en vorig jaar
-- Klantgroep en naam uit afc_klant (vaste debiteur, of S + klant_id als de debiteur voor derden betaalt).
-- Bron: afc_control_center (Floor). Contract: documentation/AFC-analyse.md in awc-dashboard.
with z as (
  select z.*, (extract(doy from z.rapportagedatum) <= extract(doy from current_date)) as ytd_venster
  from afc_control_center.afc_zending_afc_control_center z
  where not z.geannuleerd and z.rapportagedatum <= current_date
    and z.rapportagejaar >= extract(year from current_date)::int - 1
),
g as (
  select klantgroep_id, max(vaste_debiteur) as debiteurnummer,
    (array_agg(klant order by omzet_12m desc nulls last))[1] as klant
  from afc_control_center.afc_klant_afc_control_center group by 1
)
select coalesce(k.klantgroep_id, 'S' || z.klant_id) as klantgroep_id,
  coalesce(g.klant, z.klant) as klant,
  g.debiteurnummer,
  z.rapportagejaar as jaar, z.richting,
  case z.modaliteit when 'Road' then 'Weg' when 'Sea' then 'Zee' when 'Air' then 'Lucht' else 'Overig' end as modaliteit,
  z.ytd_venster,
  count(*) as zendingen,
  round(sum(coalesce(z.omzet_sprinter, 0) - coalesce(z.invoerrechten_cash, 0)), 2) as omzet,
  round(sum(coalesce(z.marge_sprinter, 0)), 2) as marge
from z
left join afc_control_center.afc_klant_afc_control_center k on k.klant_id = z.klant_id
left join g on g.klantgroep_id = k.klantgroep_id
group by 1, 2, 3, 4, 5, 6, 7
