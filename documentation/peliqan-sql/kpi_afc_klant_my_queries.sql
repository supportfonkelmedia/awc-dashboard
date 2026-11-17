-- Peliqan "My Queries".kpi_afc_klant_my_queries (table_id 1579283), stand 2026-11-16 (databaseview, live)
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | een rij per Sprinter-klant met klantstatus
-- Status volgens afc_klant (besluit 11-12-2026): Verloren > 90 dagen, Dalend < 75%, Nieuw < 365 dagen, op aanmaakdatum.
-- Let op: omzet_12m en omzet_vorige_12m zijn incl. invoerrechten (Sprinter-omzet).
-- Bron: "My Queries".afc_klant_live (live kopie van Floors afc_klant, sinds 16-11-2026). Contract: documentation/AFC-analyse.md in awc-dashboard.
select klant_id, klant, klantgroep_id, vaste_debiteur as debiteurnummer, klantstatus,
  eerste_zending, laatste_zending, dagen_sinds_laatste_zending, zendingen_totaal, zendingen_12m,
  omzet_12m, marge_12m, omzet_vorige_12m, marge_vorige_12m, modaliteiten_12m, eigenaren_12m,
  nieuwe_dienst_dit_jaar
from "My Queries".afc_klant_live_my_queries
