-- Peliqan "My Queries".kpi_betrouwbaarheid (table_id 1579305), aangemaakt 2026-11-12 (fase 0 data-integriteit); throughput, dock_to_stock en damage_rate bijgewerkt na de 7T-fix van 12-11; AFC-winrate eruit (telt sinds 12-11 de juiste pijplijn, te weinig deals toont de tegel zelf)
-- Eén rij per KPI (en eventueel scope) waarvan het cijfer niet zonder meer klopt, op basis van de
-- Peliqan-audit van 2026-11-12. Geen rij = geen bekende kanttekening.
--   niveau 'onbetrouwbaar' → kpi_oordeel zet weergave op 'onbetrouwbaar'; de tegel toont de reden, geen cijfer.
--   niveau 'let_op'        → de tegel toont het cijfer met de reden eronder.
-- scope_code NULL geldt voor alle scopes van de KPI; een rij met scope_code gaat voor.
-- Een flow is gerepareerd en gecontroleerd → rij verwijderen (en de wijziging in kpi_registry vastleggen).
SELECT
  *
FROM (VALUES
  ('throughput', 'alaw', 'let_op', 'Sinds 12 november telt een order alleen mee met een orderpicker, pallets of een pickscan; de factuurorders van 7T tellen niet meer mee. Edo bevestigt nog of dit alle fysieke uitleveringen zijn.', CAST('2026-11-12' AS DATE)),
  ('winrate', 'Verkooppijplijn', 'let_op', 'De trendlijn is opgebouwd uit de huidige stand van de deals. De opschoning in augustus vertekent de punten van 2025 en 2026.', CAST('2026-11-12' AS DATE)),
  ('bruto_marge_per_loonkosten', 'pgl1', 'let_op', 'De loonkosten missen rekening 4000 (ongeveer 48% van de AFC-loonkosten). Zolang Frits niet heeft besloten of die meetelt, kan de ratio te hoog liggen.', CAST('2026-11-12' AS DATE)),
  ('bruto_marge_per_loonkosten', 'acco', 'let_op', 'De loonkosten missen rekening 4000 (ongeveer 37% van de ACC-loonkosten). Zolang Frits niet heeft besloten of die meetelt, kan de ratio te hoog liggen.', CAST('2026-11-12' AS DATE)),
  ('bruto_marge_per_loonkosten', 'concern', 'let_op', 'De loonkosten van AFC en ACC missen rekening 4000. Zolang Frits niet heeft besloten of die meetelt, kan de ratio te hoog liggen.', CAST('2026-11-12' AS DATE)),
  ('ebitda', NULL, 'let_op', 'Correcties met een datum buiten het boekjaar vallen in januari of december, en wanneer een maand als afgesloten geldt verschilt nog per berekening. Maanden rond de jaarwisseling zijn minder betrouwbaar.', CAST('2026-11-12' AS DATE)),
  ('omzet_brug', NULL, 'let_op', 'Klanten worden over de entiteiten heen gekoppeld op zoeknaam, waardoor verschillende bedrijven met dezelfde naam als één klant tellen. De lijst met intercompany-relaties is nog niet bevestigd door Frits.', CAST('2026-11-12' AS DATE)),
  ('churn', NULL, 'let_op', 'Vertrekdata zijn in HubSpot deels in bulk ingevoerd. De datum is het moment van registratie, niet het echte vertrek.', CAST('2026-11-12' AS DATE)),
  ('triple_lob', NULL, 'let_op', 'Nog niet alle nieuwe koppelingen tussen AWC, AFC en ACC zijn beoordeeld, en de werklijst laat al beoordeelde klanten nog staan.', CAST('2026-11-12' AS DATE)),
  ('time_to_onboarding', NULL, 'let_op', 'De datum waarop een ticket de fase Onboard bereikt is vaak leeg, en het aantal trajecten is klein.', CAST('2026-11-12' AS DATE)),
  ('acc_dossiers', NULL, 'let_op', 'Telt e-mailtickets, niet alleen dossiers, met dubbele onderwerpen ertussen. De 3.776 open tickets tellen niet mee.', CAST('2026-11-12' AS DATE)),
  ('acc_doorlooptijd', NULL, 'let_op', 'Gebaseerd op e-mailtickets in plaats van dossiers. De 3.776 open tickets tellen niet mee, dus de doorlooptijd kan te laag liggen.', CAST('2026-11-12' AS DATE)),
  ('dock_to_stock', NULL, 'let_op', 'Alleen inbounds met een verplaatsing tellen mee, ongeveer 60% van alle inbounds. Edo bevestigt nog of de rest terecht buiten de meting valt.', CAST('2026-11-12' AS DATE)),
  ('damage_rate', NULL, 'let_op', 'Welke manco-reden als schade telt, is nog niet bevestigd door Edo.', CAST('2026-11-12' AS DATE)),
  ('afc_marge_per_zending', NULL, 'let_op', 'Bedragen worden bij facturatie aangevuld. Voor oktober staan nog 147 zendingen open, dus het cijfer kan nog veranderen.', CAST('2026-11-12' AS DATE)),
  ('enps', NULL, 'let_op', 'Invoer via dit dashboard komt nog niet aan in de cijfers. Alleen invoer via de invoerapp in Peliqan telt.', CAST('2026-11-12' AS DATE)),
  ('ab_players', NULL, 'let_op', 'Invoer via dit dashboard komt nog niet aan in de cijfers. Alleen invoer via de invoerapp in Peliqan telt.', CAST('2026-11-12' AS DATE))
) AS v(kpi_code, scope_code, niveau, reden, vastgesteld_op)
