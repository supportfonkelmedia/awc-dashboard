# Bouwbriefing KPI-dashboard AWC, deel 1

Voor Fonkel. Dit deel bevat de twee KPI's die volledig zijn uitgewerkt en getoetst: winrate en bruto marge per loonkosten. Per KPI staat de exacte bron, de tabellen en velden, de rekenregel en controlecijfers.

Alle data komt uit de Peliqan data warehouse (PostgreSQL). Twee schema's zijn hier relevant: `hubspot_v2` en `cashweb`.

De controlecijfers onderaan elke KPI zijn berekend op de huidige data. Als jullie tegel dezelfde uitkomst geeft, staat de rekenregel goed.

---

## KPI 1. Winrate

### Bron

Schema `hubspot_v2`.

**Tabel `deals`** (hoofdtabel):

| Veld | Gebruik |
|---|---|
| `id` | unieke deal |
| `pipeline` | pijplijn-id, nodig om te splitsen |
| `hs_is_closed_won` | tekst 'true' of 'false', gewonnen |
| `hs_is_closed_lost` | tekst 'true' of 'false', verloren |
| `hs_is_closed` | gesloten ja/nee, alleen voor controle |
| `closedate` | sluitdatum, voor de periode-indeling |
| `amount` | dealwaarde, optioneel voor een gewogen variant |

**Tabel `deals_pipeline`** (voor de namen):

| Veld | Gebruik |
|---|---|
| `id` | koppelt aan `deals.pipeline` |
| `label` | leesbare naam van de pijplijn |

### Rekenregel

```
winrate = aantal gewonnen / (aantal gewonnen + aantal verloren)
```

- Gewonnen: `hs_is_closed_won = 'true'`
- Verloren: `hs_is_closed_lost = 'true'`
- Open deals tellen NIET mee in de noemer.

### Belangrijk

- Reken op deze twee vlaggen, **niet** op `dealstage` of op een stagenaam. De huidige tegel staat op 0 procent omdat er op een stagenaam wordt gerekend. Er lopen twee pijplijnen door elkaar waarin de gewonnen stap een andere naam en een ander id heeft.
- Toon de winrate **per pijplijn**, gescheiden. De twee verschillen sterk en mogen niet worden opgeteld.
- Periode: per kwartaal op basis van `closedate`.

### Controlecijfers

Op de volledige historie:

| Pijplijn | Gewonnen | Verloren | Winrate |
|---|---|---|---|
| Verkooppijplijn | 55 | 148 | 27,1% |
| AFC Verkooplijn | 16 | 8 | 66,7% |

### Kanttekening

Er staan veel deals open die nooit zijn afgesloten (513 in de Verkooppijplijn, 175 in de AFC-lijn). Die worden aan onze kant opgeschoond. Met bovenstaande formule beïnvloeden ze de winrate niet, omdat open deals buiten de noemer blijven.

---

## KPI 2. Bruto marge per loonkosten

### Bron

Schema `cashweb`.

**Tabel `ledger_mutations`** (alle grootboekboekingen):

| Veld | Gebruik |
|---|---|
| `admin_code` | entiteit, hierop filteren en groeperen |
| `account_number` | grootboekrekening, bepaalt omzet/inkoop/loon |
| `amount` | bedrag, **tekstveld met komma als decimaalteken** |
| `debit_credit` | 'C' of 'D', bepaalt het teken |
| `book_year` | boekjaar |
| `book_period` | periode/maand |
| `book_date` | boekdatum |

**Tabel `administrations`** (voor de namen):

| Veld | Gebruik |
|---|---|
| `code` | koppelt aan `ledger_mutations.admin_code` |
| `name` | leesbare naam van de entiteit |

### Entiteiten

| admin_code | Entiteit |
|---|---|
| `alaw` | Amsterdam Warehouse Company (AWC) |
| `pgl1` | Amsterdam Freight Company (AFC) |
| `acco` | Amsterdam Customs Company (ACC) |

Sluit de administratie `demo` altijd uit, dat is testdata. Er komen ook andere administraties binnen via dezelfde koppeling (fiscale entiteiten, holding); die horen niet in deze KPI.

### Twee technische aandachtspunten

1. **Het bedrag is tekst met een komma.** Converteer eerst: `REPLACE(amount, ',', '.')::numeric`
2. **Reken met het teken.** Bij `debit_credit = 'C'` telt het bedrag positief, bij `'D'` negatief. Omzet staat credit, kosten staan debet. Zonder dit klopt de marge niet.

### Rekenregel

```
omzet       = som van rekeningen die met 8 beginnen (creditkant)
inkoop      = som van rekeningen die met 6 beginnen (debetkant)
bruto marge = omzet - inkoop
loonkosten  = som van de loonrekeningen (per entiteit, zie hieronder)

KPI = bruto marge / loonkosten
```

De uitkomst is een verhouding: hoeveel euro brutomarge staat er tegenover elke euro loon.

### Loonrekeningen per entiteit

Deze lijsten zijn aangeleverd door de financiële afdeling.

| Entiteit | Loonrekeningen |
|---|---|
| AWC (`alaw`) | 4000, 4001, 4010, 40100, 40101, 4110, 4130, 4514 |
| AFC (`pgl1`) | 4010, 4011, 4110, 41100, 4130, 4512, 4514 |
| ACC (`acco`) | 4010, 4011, 4110, 41100, 4130, 4512, 4514 |

**Bouw deze lijsten instelbaar, niet vast in de code.** Er loopt nog een besluit over de vraag of ingehuurde arbeid moet meetellen. Als dat besluit valt, moeten er rekeningen bij of af kunnen zonder dat de tegel herbouwd wordt. Dat besluit verandert de uitkomst aanzienlijk, dus dit is geen detail.

Let daarnaast op: bij AFC en ACC zijn 4130 (pensioenlasten, werkgeversdeel) en 4512 (reis- en verblijfkosten) maar gedeeltelijk loon. Op die rekeningen staat ook ander verkeer. Maak het bedrag op deze twee rekeningen apart zichtbaar, zodat het management kan zien wat het effect is.

### Periode en afsluiting

Bouw per maand en per entiteit, met een totaal.

Toon de laatste maand pas als definitief zodra die is afgesloten:

- AWC en ACC zijn ongeveer een maand na afloop bij.
- AFC duurt langer, door inkoop die betrekking heeft op eerdere periodes.

### Controlecijfers

Jaartotalen in euro's, met de loonrekeningen zoals hierboven:

| Entiteit | Jaar | Bruto marge | Loonkosten | KPI |
|---|---|---|---|---|
| AWC | 2024 | 7.868.115 | 1.236.694 | 6,36 |
| AWC | 2025 | 9.558.361 | 1.631.613 | 5,86 |
| AFC | 2024 | 1.307.010 | 348.912 | 3,75 |
| AFC | 2025 | 1.416.285 | 367.703 | 3,85 |
| ACC | 2024 | 341.524 | 132.623 | 2,58 |
| ACC | 2025 | 402.812 | 140.243 | 2,87 |

### Openstaand punt

Wij checken nog of rubriek 7 ook als kostprijs meetelt bij de inkoop. Op dit moment rekenen we alleen met rubriek 6. Rubriek 7 is nauwelijks gevuld, dus we verwachten geen verschil, maar we koppelen terug zodra dit bevestigd is.

---

## Algemene opmerkingen

- Beide KPI's draaien volledig op de warehouse en hebben geen extra koppelingen nodig.
- De HubSpot-sync liep één dag mis in juli en draait daarna weer normaal. De Cashweb-sync is stabiel.
- Er komt nog een deel 2 met de KPI's churn ICP en procent Triple LOB. Die zijn inhoudelijk uitgewerkt maar wachten nog op een definitiebesluit aan onze kant.
