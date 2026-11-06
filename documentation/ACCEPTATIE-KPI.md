# KPI-dashboard — acceptatietest (na bouw)

Uitvoeren **nadat** `PELIQAN_KPI_DATA_URL` live is en alle schermen data tonen. Leidend: [Overdracht KPI-dashboard Fonkel.md](Overdracht%20KPI-dashboard%20Fonkel.md) hoofdstuk **Acceptatietest**.

## Voorbereiding

**Lokaal zonder Peliqan:** in `APP_ENV=local` laadt `/kpi/*` automatisch **demo-fixtures** (acceptatie-baseline 22 sep 2026) als `PELIQAN_KPI_DATA_URL` leeg is. Kopbalk toont badge **Demo-data**. Forceer altijd fixtures met `KPI_USE_FIXTURE=true`.

1. Noteer tijdstip en lees op dat moment `kpi_oordeel_my_queries` (of JSON via API).
2. **JSON (ingelogd):** `GET /kpi/api/screens/{scherm}` — zelfde payload als `GET /kpi/peliqan/data?bundle=screen&scherm=…`. Drill: `GET /kpi/api/drill?views=kpi_bm_maand,…`. Controles: `GET /kpi/api/controles`.
3. Open mockups: [kpi-dashboard-mockups/](kpi-dashboard-mockups/).
4. Per scherm: screenshot + checklist hieronder.

## Routes (7 schermen)

| Scherm | URL |
| --- | --- |
| Strategisch | `/kpi/strategisch` |
| Operationeel | `/kpi/operationeel` |
| Tactisch | `/kpi/tactisch` |
| AWC | `/kpi/awc` |
| AFC | `/kpi/afc` |
| ACC | `/kpi/acc` |

## Structuur (alle schermen)

- [ ] Tegels/banners/secties = volgorde `kpi_tegel_config.positie`
- [ ] Header: datacontroles-telling = som `kpi_controles.status`
- [ ] Bijgewerkt = oudste `bron_bijgewerkt` van getoonde tegels (NL-tijd)
- [ ] Geen `pglh` in UI, tooltips, netwerk JSON
- [ ] Geen getal op tegels met staat ≠ `meetwaarde`
- [ ] Drill-down views in volgorde `drill_views`

## Getallen (eerste baseline 22 sep 2026)

Vul aan per tegel uit Overdracht § Tegels met een getal — afwijking in format (komma, pp, mln) = fout.

- [ ] Strategisch: omzetbrug, BM/loon, Triple LOB, winrate, churn, EBITDA, …
- [ ] Operationeel / AWC / AFC / ACC: zie Overdracht-tabel

## Trend steekproeven

- [ ] `ebitda/concern` juli 2026 definitief; augustus voorlopig
- [ ] Sprinter `afc_zendingen` augustus onvolledig
- [ ] `acc_dossiers` vier series september voorlopig

## Invoer (staging MariaDB)

- [ ] eNPS / A/B via modal → `kpi_handmatige_invoer`
- [ ] Doel via modal → `kpi_doelen_invoer`
- [ ] `php artisan kpi:export-invoer --pretty` voor Peliqan-sync

## Livegang

- [x] Redirects `/mt-dashboard` → `/kpi/strategisch` (en `/awc-dashboard`, `/afc-dashboard`, `/acc-dashboard`)
- [x] Legacy `/mt-dashboard/legacy` e.a. verwijderd
- [ ] Chloë bevestigt sync invoer/doelen in `kpi_invoer`
