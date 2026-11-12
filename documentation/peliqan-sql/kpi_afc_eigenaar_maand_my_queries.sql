-- Peliqan "My Queries".kpi_afc_eigenaar_maand_my_queries (table_id 1579281), stand 2026-11-12
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | maand x dossiereigenaar x afdeling x richting x ytd_venster, lopend en vorig jaar
-- Bron: afc_control_center.afc_zending (Floor). Contract: documentation/AFC-analyse.md in awc-dashboard.
with z as (
  select *, (extract(doy from rapportagedatum) <= extract(doy from current_date)) as ytd_venster
  from afc_control_center.afc_zending_afc_control_center
  where not geannuleerd and rapportagedatum <= current_date
    and rapportagejaar >= extract(year from current_date)::int - 1
)
select rapportagemaand as maand, rapportagejaar as jaar,
  coalesce(eigenaar, '(onbekend)') as eigenaar, afdeling, richting, ytd_venster,
  count(*) as zendingen,
  round(sum(coalesce(omzet_sprinter, 0) - coalesce(invoerrechten_cash, 0)), 2) as omzet,
  round(sum(coalesce(marge_sprinter, 0)), 2) as marge
from z group by 1, 2, 3, 4, 5, 6
