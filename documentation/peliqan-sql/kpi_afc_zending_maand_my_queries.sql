-- Peliqan "My Queries".kpi_afc_zending_maand_my_queries (table_id 1579280), stand 2026-11-12
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | maand x modaliteit x richting x ytd_venster
-- Bron: afc_control_center.afc_zending (Floor). Omzet excl. invoerrechten en btw = Sprinter-omzet min invoerrechten uit Cash.
-- ytd_venster: rapportagedatum op of voor dezelfde dag van het jaar als vandaag (jaar t/m vandaag vergelijken).
-- Contract: documentation/AFC-analyse.md in awc-dashboard. Kolommen niet hernoemen zonder de pagina aan te passen.
with z as (
  select *, (extract(doy from rapportagedatum) <= extract(doy from current_date)) as ytd_venster
  from afc_control_center.afc_zending_afc_control_center
  where not geannuleerd and rapportagedatum >= date '2024-01-01' and rapportagedatum <= current_date
)
select rapportagemaand as maand,
  rapportagejaar as jaar,
  extract(month from rapportagemaand)::int as maandnummer,
  case modaliteit when 'Road' then 'Weg' when 'Sea' then 'Zee' when 'Air' then 'Lucht' else 'Overig' end as modaliteit,
  richting,
  ytd_venster,
  count(*) as zendingen,
  sum(case when status_code = 'O' then 1 else 0 end) as zendingen_open,
  round(sum(coalesce(omzet_sprinter, 0) - coalesce(invoerrechten_cash, 0)), 2) as omzet,
  round(sum(coalesce(omzet_sprinter, 0)), 2) as omzet_incl_invoerrechten,
  round(sum(coalesce(marge_sprinter, 0)), 2) as marge
from z group by 1, 2, 3, 4, 5, 6
