-- Peliqan "My Queries".kpi_afc_resultaat_maand_my_queries (table_id 1579285), stand 2026-11-12
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | resultaat volgens Cash per maand (pgl1), boekjaar leidend
-- Bron: afc_control_center.afc_resultaat_maand (Floor). Contract: documentation/AFC-analyse.md in awc-dashboard.
select periode_id, boekjaar, maandnummer, maand, omzet, invoerrechten_doorbelast, omzet_incl_invoerrechten,
  btw_verkoop, kostprijs, kostprijs_sim_cargo, kostprijs_svz, brutomarge, brutomarge_pct, bedrijfskosten,
  resultaat_humber, resultaat_voor_belasting, vennootschapsbelasting, resultaat_na_belasting, periode_afwijkend
from afc_control_center.afc_resultaat_maand_afc_control_center
