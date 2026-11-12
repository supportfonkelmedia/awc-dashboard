-- Peliqan "My Queries".kpi_afc_klant_my_queries (table_id 1579283), stand 2026-11-12
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | een rij per Sprinter-klant met klantstatus
-- Status volgens afc_klant (besluit 11-12-2026): Verloren > 90 dagen, Dalend < 75%, Nieuw < 365 dagen, op aanmaakdatum.
-- Let op: omzet_12m en omzet_vorige_12m zijn incl. invoerrechten (Sprinter-omzet).
-- Bron: afc_control_center.afc_klant (Floor). Contract: documentation/AFC-analyse.md in awc-dashboard.
select klant_id, klant, klantgroep_id, vaste_debiteur as debiteurnummer, klantstatus,
  eerste_zending, laatste_zending, dagen_sinds_laatste_zending, zendingen_totaal, zendingen_12m,
  omzet_12m, marge_12m, omzet_vorige_12m, marge_vorige_12m, modaliteiten_12m, eigenaren_12m,
  nieuwe_dienst_dit_jaar
from afc_control_center.afc_klant_afc_control_center
