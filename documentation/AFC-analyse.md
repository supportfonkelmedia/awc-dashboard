# AFC-analyse: datacontract en Peliqan-views

Pagina `/kpi/afc/analyse` (MT eerst, later teamleads). Vertaling van Floors pagina
"AFC omzet & marge" naar het dashboard. De pagina leest zes views via de bestaande drill-route
(`bundle=drill`). Lokaal en zonder Peliqan-configuratie komt demo-data uit
`AfcAnalyseFixture` met precies dezelfde kolommen.

## Bron

Schema `afc_control_center` in dw_2401 (Floor, opgebouwd 11-11-2026). Dagelijkse replica's
`<tabel>_afc_control_center` tussen 08:45 en 09:15 UTC. De views hieronder komen in
`"My Queries"` (replica `_my_queries`, elk uur), zodat de handler geen ander schema hoeft te lezen.

## Besluiten (Chloë, 12-11-2026)

- Klantstatus volgens `afc_klant`: Verloren = laatste zending > 90 dagen (Eenmalig bij 1 zending),
  Nieuw = eerste zending < 365 dagen, Dalend = omzet 12 mnd < 75% van de 12 mnd daarvoor.
- Omzet overal excl. invoerrechten en btw (Sprinter-omzet min invoerrechten uit Cash).
- Per dossiereigenaar mag het MT zien.
- Aansluiting Sprinter/Cash en Sim Cargo/SVZ: ingeklapt financieel blok onderaan.

## Aansluiting (gecontroleerd 12-11-2026, alleen lezen)

- Cash: `afc_resultaat_maand` en `kpi_bm_maand` / `kpi_ebitda_maand` (pgl1) zijn per maand gelijk van
  februari t/m oktober 2026. Verschil zit in januari (boekingen uit een eerder boekjaar: 42 regels,
  brutomarge −19.415 tegen 2.853) en in november/december (nog niet afgesloten, december heeft al
  boekingen). Over 2024 en 2025 is het omzetverschil kleiner dan 0,05%.
- Sprinter: `afc_zending` en `kpi_afc_sprinter_maand` zijn per maand gelijk t/m augustus 2026.
  Kleine verschillen vanaf september komen alleen door de ververstijd (dagelijks tegen elk uur).
  Oktober staat op "volledig" terwijl 158 zendingen nog open (O) staan.

## Views

### 1. `kpi_afc_zending_maand`
Maand × modaliteit × richting × `ytd_venster`. `ytd_venster` = rapportagedatum valt op of vóór
dezelfde dag van het jaar als vandaag, zodat "jaar t/m vandaag" eerlijk met vorig jaar te vergelijken is.

```sql
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
```

### 2. `kpi_afc_eigenaar_maand`
Maand × dossiereigenaar × afdeling × richting × `ytd_venster`, lopend en vorig jaar.

```sql
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
```

### 3. `kpi_afc_klant_jaar`
Klantgroep × jaar × richting × modaliteit × `ytd_venster`, lopend en vorig jaar. Klantgroep en naam uit
`afc_klant` (vaste debiteur, of S + klant_id als de debiteur voor derden betaalt).

```sql
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
```

### 4. `kpi_afc_klant`
Eén rij per Sprinter-klant met status. Rechtstreeks uit `afc_klant`.

```sql
select klant_id, klant, klantgroep_id, vaste_debiteur as debiteurnummer, klantstatus,
  eerste_zending, laatste_zending, dagen_sinds_laatste_zending, zendingen_totaal, zendingen_12m,
  omzet_12m, marge_12m, omzet_vorige_12m, marge_vorige_12m, modaliteiten_12m, eigenaren_12m,
  nieuwe_dienst_dit_jaar
from afc_control_center.afc_klant_afc_control_center
```

### 5. `kpi_afc_klant_retentie_jaar`
Per kalenderjaar (aanmaakdatum) ten opzichte van het jaar ervoor.

```sql
with z as (
  select klant_id, extract(year from aanmaakdatum)::int as jaar, count(*) as n,
         sum(coalesce(omzet_sprinter, 0) - coalesce(invoerrechten_cash, 0)) as omzet
  from afc_control_center.afc_zending_afc_control_center
  where not geannuleerd and klant_id is not null and aanmaakdatum <= current_date
  group by 1, 2
),
f as (select klant_id, min(jaar) as eerste_jaar from z group by 1),
j as (select distinct jaar from z),
c as (
  select j.jaar,
    count(distinct cur.klant_id) as actieve_klanten,
    count(distinct case when cur.klant_id is not null and prev.klant_id is not null then cur.klant_id end) as behouden,
    count(distinct case when prev.klant_id is not null and cur.klant_id is null then prev.klant_id end) as weggevallen,
    count(distinct case when cur.klant_id is not null and f.eerste_jaar = j.jaar then cur.klant_id end) as nieuw,
    count(distinct case when cur.klant_id is not null and prev.klant_id is null and f.eerste_jaar < j.jaar then cur.klant_id end) as teruggekeerd,
    count(distinct case when cur.n = 1 then cur.klant_id end) as met_1_zending,
    count(distinct prev.klant_id) as actief_vorig_jaar,
    round(sum(case when prev.klant_id is not null and cur.klant_id is null then prev.omzet else 0 end), 2) as omzet_weggevallen_vorig_jaar,
    round(sum(case when cur.klant_id is not null and f.eerste_jaar = j.jaar then cur.omzet else 0 end), 2) as omzet_nieuwe_klanten
  from j
  cross join (select distinct klant_id from z) k
  left join z cur on cur.klant_id = k.klant_id and cur.jaar = j.jaar
  left join z prev on prev.klant_id = k.klant_id and prev.jaar = j.jaar - 1
  left join f on f.klant_id = k.klant_id
  group by 1
)
select *,
  round(100.0 * behouden / nullif(actief_vorig_jaar, 0), 1) as retentie_pct,
  round(100.0 * weggevallen / nullif(actief_vorig_jaar, 0), 1) as churn_pct,
  (jaar = extract(year from current_date)::int) as lopend_jaar
from c
```

### 6. `kpi_afc_resultaat_maand`
Resultaat volgens Cash per maand. Rechtstreeks uit `afc_resultaat_maand` (boekjaar leidend).

```sql
select periode_id, boekjaar, maandnummer, maand, omzet, invoerrechten_doorbelast, omzet_incl_invoerrechten,
  btw_verkoop, kostprijs, kostprijs_sim_cargo, kostprijs_svz, brutomarge, brutomarge_pct, bedrijfskosten,
  resultaat_humber, resultaat_voor_belasting, vennootschapsbelasting, resultaat_na_belasting, periode_afwijkend
from afc_control_center.afc_resultaat_maand_afc_control_center
```

## Stand in Peliqan

Aangemaakt op 12-11-2026 in `"My Queries"` (dw_2401):

| View (query in Peliqan heet nu `<view>_my_queries`) | table_id | Rijen bij aanmaken |
|---|---|---|
| kpi_afc_zending_maand | 1579280 | 299 |
| kpi_afc_eigenaar_maand | 1579281 | 660 |
| kpi_afc_klant_jaar | 1579282 | 1321 |
| kpi_afc_klant | 1579283 | 641 |
| kpi_afc_klant_retentie_jaar | 1579284 | 4 |
| kpi_afc_resultaat_maand | 1579285 | 36 |

De handler leest `"My Queries".<view>_my_queries`. In plaats van een replica (kopie per uur) zijn
de zes queries als **databaseview** aangemaakt (`create_as_view`) en hernoemd naar `<view>_my_queries`.
In Peliqan heten de query-tabellen dus `kpi_afc_..._my_queries`; dat is bewust, zo heet de view in
de database precies zoals de handler hem zoekt. Een view rekent bij elke aanvraag op de replica's van
`afc_control_center` (dagelijks 08:30 tot 09:15 UTC ververst); Laravel cachet het antwoord een uur.
Zet hier geen replica op: die zou `..._my_queries_my_queries` heten en niet gelezen worden.

Handler: app 17395 (`/kpi/data`) op v8 (`2026-11-12-kpi-v8-afc-analyse`), gelijk aan
`peliqan_kpi_api_handler.py`. De vorige versie (v7) staat in de commit ervoor.

## Nog te doen

1. Eind-tot-eind controleren op de testserver (lokaal ontbreekt de Peliqan-JWT).
2. `kpi_afc_sprinter_maand` herbouwen op `afc_zending`, zodat er één Sprinter-keten is.
3. Teams: de teamleads krijgen later een eigen dashboard met tegels uit dit scherm; eigenaar → team volgt.

## AFC-tegels (12-11-2026)

- **Quote conversion (tegel 8) is live.** Gewonnen / (gewonnen + afgewezen + verlopen), offertes aangemaakt
  in de 12 maanden t/m de laatste afgesloten maand. Status uit `afc_offerte.status_afgeleid` (Floor).
  Oktober 2026: 47,4% (n = 456). Bouw: view `kpi_afc_offerte_maand_my_queries` (1579304), extra rij in
  `kpi_afc_sprinter_tegel`, regel 21 in `kpi_registry`, reeks `t_off` in `kpi_trend`, AFC-positie 8 in
  `kpi_tegel_config`, handler v9. Live SQL in `peliqan-sql/`; de stand ervoor staat in de git-historie.
- **Sync:** sinds 12-11-2026 haalt de dagelijkse Sprinter-sync (app 18062, 02:30) na de zendingen ook alle
  offertes en bedrijven opnieuw op. Script en backup: `peliqan-apps/sprinter_api_sync_dagelijks.py`.
  Kolomtypes komen uit een vaste lijst (stand 12-11): de live opvraag van information_schema is vanuit een
  Peliqan-app niet toegestaan. Nieuwe kolommen uit de API laat de writer zelf aanmaken.
- **On-time delivery (tegel 9) blijft in opbouw.** Sprinter levert geen geplande of werkelijke afleverdatum;
  zendingen hebben alleen mijlpaal-ID's zonder tijd. Er zijn legs of mijlpalen per zending nodig.
