# Drill-downs per tegel en integriteitscheck

Stand 2026-11-12 19:00 UTC. Elke tegel met een waarde opent een drawer met de views uit
`kpi_tegel_config.drill_views`. De drawer stuurt de scope van de tegel mee (`scope=alaw`,
`scope=AFC - Verkooplijn`, ...); handler v10 filtert daarop (`scope_code`, `admin_code` of
`pipeline`). Concern zonder eigen rijen (bruto marge, kosten) toont alle entiteiten.

## Welke tegel welke drill heeft

| Tegel | Schermen | Drill-views |
|---|---|---|
| EBITDA concern | Strategisch | kpi_ebitda_maand, kpi_kosten_maand, kpi_handmatig |
| EBITDA per entiteit | AWC, AFC, ACC | kpi_ebitda_maand, kpi_kosten_maand |
| Bruto marge per loonkosten | Strategisch, AWC, AFC, ACC | kpi_bm_maand |
| Omzetbrug / Omzet en klanten | Strategisch, AWC, AFC, ACC | kpi_omzetbrug, kpi_omzetbrug_klant (+ _top op Strategisch) |
| Triple LOB | Strategisch | kpi_triple_lob_maand, kpi_triple_lob_te_controleren |
| Winrate | Strategisch, Operationeel, AFC | **kpi_winrate_deal**, kpi_winrate_maand (+ _fases op Strategisch) |
| Churn | Strategisch, Operationeel | **kpi_churn_klant**, kpi_churn_kwartaal |
| Time to onboarding | Operationeel | kpi_onboarding_kwartaal |
| Dock-to-stock | AWC, Operationeel | kpi_d2s_maand |
| Throughput, Damage rate | AWC | kpi_awc_ops_maand (+ kpi_awc_schade_klant) |
| Dossiers, Doorlooptijd | ACC, Operationeel | kpi_acc_dossiers_maand, kpi_acc_doorlooptijd_maand |
| Zendingen, Modal split, Marge per zending | AFC | kpi_afc_sprinter_maand, plus link naar de AFC-analyse |
| Quote conversion | AFC | kpi_afc_offerte_maand, plus link naar de AFC-analyse |

Geen drill (geen data om in te duiken): OTIF, en de vaste tegels in opbouw / in validatie /
niet meetbaar (First time right, On-time delivery, Inventory accuracy, Perfect order rate,
Storage lead time, ICP-interacties, Client requests per LOB, Bezettingsgraad).

Nieuw op 2026-11-12: `kpi_churn_klant_my_queries` (table 1579315) en
`kpi_winrate_deal_my_queries` (1579319), DB-views, SQL in `peliqan-sql/`. Eén rij per vertrokken
klant / deal, met `tegelvenster` (welke rijen de tegel telt) en `bulkdag` (10 of meer op één dag).

## Integriteitscheck tegel = drill (2026-11-12, replica's van 18:51-18:53 UTC)

| Tegel | Tegel | Drill | Uitkomst |
|---|---|---|---|
| EBITDA AWC / AFC / ACC / concern (12 mnd t/m 09-2026) | 676.516 / 599.273 / 111.710 / 1.387.499 | ebitda_12m sep-2026: idem | gelijk; ook vorig jaar gelijk; gelijk aan onafhankelijke herberekening uit cashweb op book_period_ledger |
| EBITDA = omzet - kostengroepen (12 mnd) | | kpi_kosten_maand | AWC exact, AFC/ACC binnen 4 euro (afronding per maand) |
| Bruto marge per loonkosten AWC / AFC / ACC / concern | 2,21 / 3,57 / 2,54 / 2,29 | som bruto marge / som loonkosten in het venster | gelijk |
| Omzetbrug (4 scopes) | eind / start | start + nieuw + gegroeid - gekrompen - verloren = eind; klantdrill telt op | gelijk (klantdrill binnen 15 euro afronding) |
| Triple LOB | 6,7% (40/596), vorige maand 7,6% | triple_lob_maand sep/aug | gelijk; 2 matches te controleren = drill |
| Winrate Verkooppijplijn | 46,2% (54/117), vorige 44,2% | winrate_maand 'vandaag' en winrate_deal 'telt mee' | gelijk; 49 van de 63 verloren op bulkdag 21-08 |
| Winrate AFC | leeg (6 beslist, minimum 20) | 6 verloren, 0 gewonnen | gelijk |
| Churn | 65 (vorige 46), 48 op bulkdagen | churn_klant per venster; churn_kwartaal per kwartaal | gelijk, ook per kwartaal |
| Dock-to-stock | 95,1% (780/820) | d2s_maand okt | gelijk |
| Damage rate | 4,1% (55/1350) | awc_ops_maand okt | gelijk |
| Throughput | 6.085 | awc_ops_maand okt | gelijk (zie noot) |
| AFC zendingen / modal split / marge per zending | 1.116 / 88,7% / 154,48 | afc_sprinter_maand okt | gelijk (voorlopig: open zendingen) |
| Quote conversion | 47,4% | afc_offerte_maand okt | gelijk |
| ACC dossiers | 9.227 (3535/3348/813/1531) | acc_dossiers_maand 2026 | gelijk per soort |
| ACC doorlooptijd | 2,7 dagen, n=5692 | acc_doorlooptijd_maand: 5692 afgerond | n gelijk; mediaan over het jaar, drill per maand |
| Time to onboarding | 53,9 dagen, n=46 | onboarding_kwartaal: 46 afgerond | n gelijk |

Trendlijnen (`kpi_trend`) eindigen op de tegelwaarde voor alle KPI's met hetzelfde venster
(hercontrole 19:52-snapshot). Omzetbrug AWC en concern: trend 20 euro lager (vorig jaar 398 euro).
Geen afronding maar definitie: kpi_omzetbrug laat klanten weg met netto omzet <= 0 in beide
vensters (`WHERE vorig > 0 OR nu > 0`, vooral creditnota's); kpi_trend telt ze mee. ACC-doorlooptijd, dossiers, churn en
onboarding hebben bewust een ander venster in de trend (maand of kwartaal) dan op de tegel.

Hercontroles na de laatste commit (19:52-snapshot):
- EBITDA = omzet - kostengroepen: AWC 0, AFC -2, ACC +4, concern +2 euro. Afronding bewezen: alle
  599 rijen in kpi_kosten_maand zijn hele euro's (per maand en groep afgerond); ACC rechtstreeks uit
  cashweb op book_period_ledger is exact 111.710 = tegel.
- End-to-end, Peliqan-runtime: een tijdelijke Peliqan-app (18122, na afloop verwijderd) draaide de
  v10-handlercode in de echte runtime met precies de verzoeken van de drawer: elk scherm, elke tegel
  met drill, plus de entiteitkeuze op Strategisch. 48 aanroepen, 0 fouten, geen lege of ontbrekende
  views, en geen scope-lek (geen rij van een andere entiteit of pijplijn in een gefilterde drill).
- End-to-end, Laravel-kant: `tests/Feature/KpiDrillPeliqanRouteTest.php` speelt die echte
  v10-antwoorden (namen geanonimiseerd) af via de echte controller, service en PeliqanClient. Het
  verzoek gaat met views, scope en de JWT-header naar Peliqan, het antwoord komt ongewijzigd terug, en
  scope zit in de cachesleutel (AWC komt nooit uit de AFC-cache).
- Wat dan nog overblijft is alleen de echte HTTP-hop Laravel -> api.eu.peliqan.io met het
  productietoken; die volgt bij de eerstvolgende deploy (testserver nu geblokkeerd).
- December 2026 in de EBITDA-drill (vooruitgedateerde boekingen): op 13-11 bij de bron opgelost
  (kpi_ebitda_maand en kpi_kosten_maand eindigen op de huidige maand), 12-maands-EBITDA ongewijzigd.
  De drawer verbergt maanden na deze maand bovendien zelf, met een melding (7d6b321).
- Echte HTTP-hop met het productietoken: Chloë besloot 13-11 die live te testen zodra dit naar main gaat.
- Hercontrole 13-11 06:51: tegel = drill voor EBITDA (4x), churn 65 en winrate 45,7% (venster
  schuift dagelijks); AFC-winrate leeg (6 beslist, minimum 20).
- Let op voor de AFC-analyse: Floors afc_control_center volgt de documentperiode, niet book_period_ledger.
  Omzet sluit elke maand aan op kpi_bm_maand; bruto marge pgl1 wijkt af in jan/feb (1.810) en sep/okt (256).
- Peliqan-kant end-to-end: de 42 queries die handler v10 bouwt voor elke (drill-view, scope) uit de
  live tegelconfig draaien allemaal foutloos op dw_2401 en geven rijen terug (max 723, onder de limiet
  2000, dus niets afgekapt). Niet getest: de HTTP-route met JWT vanaf de testserver (deploy geblokkeerd;
  sinds v10 geen API-aanroepen in de endpointlog).
- Periodewissel voor omzet: kpi_klant_omzet_maand staat sinds 18:37 op book_period_ledger. Omzetbrug
  bleef gelijk, en dat klopt: 8xxx-omzet verschuift alleen bij AWC, met een document van 30.000 euro
  (511420, doorbelasting aan Amsterdam Customs Company, zoek CUSTOMS). Dat staat op de
  intercompany-lijst en telt in brug en trend niet mee.
- OTIF en de vaste tegels tonen geen getal (kpi_oordeel.waarde leeg, staat in opbouw / in validatie /
  niet meetbaar); er is niets om naar door te klikken of op te tellen.

Noten:
- Throughput zakte op 12-11 van 15.729 naar 6.085 orders: `kpi_7t_naar_warehouse` (app 13737)
  telt sindsdien alleen fysieke uitleveringen; 7T maakt bij facturatie ook logistieke orders zonder
  picker, pickscan of pallets, die outbound ~2,5x te hoog maakten.
  Edo bevestigde op 13-11 dat er geen order weggaat zonder orderpicker; de let_op-rij is eruit.
  Controle tegen de telling van Mark (13-11): zendingen in 7T (dbo.Zendingen, nummers 517331 t/m 573851,
  ruim 55.000 in 2026) liggen per maand 2-9% onder de tegel (okt 5.870 zendingen tegen 6.085 orders;
  een zending kan meer orders bevatten). Inkomend telt de tegel al de voorraad-derden-ontvangsten
  (Spare_Orders gelost, okt 1.350; ordernummer nu 128.701).
- Tegel en drill lezen elk hun eigen replica (ieder uur rond :51). Vlak na een bronwijziging kunnen
  ze tot een uur uiteenlopen; dat zagen we bij throughput en AFC (17:51 / 18:08 bronupdate).
- `kpi_ebitda_maand` heeft in Peliqan `ebitda` als primary key. Onschuldig (de replica wordt elk uur
  volledig herbouwd), maar bij twee gelijke bedragen faalt alleen het PK-statement.
