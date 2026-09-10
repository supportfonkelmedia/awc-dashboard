# Bouwbriefing KPI-dashboard AWC, deel 2

Voor Fonkel. Dit deel bevat de KPI procent Triple LOB. De opzet wijkt bewust af van deel 1: in plaats van vaste controlecijfers krijgen jullie een validatiequery. Zo kunnen jullie op elk moment zelf toetsen, ook als er in de bron iets is opgeschoond.

Bron: Peliqan data warehouse (PostgreSQL), schema `cashweb`.

## Wat de KPI meet

Het aandeel klanten dat omzet heeft bij alle drie de onderdelen: Warehouse (AWC), Freight (AFC) en Customs (ACC).

## Waarom er een tussentabel nodig is

De drie onderdelen zijn drie aparte administraties in Cashweb. Elke administratie heeft een eigen klantnummer dat bij 1 begint, dus dezelfde klant is niet vanzelf te herkennen. Het btw-nummer werkt daar niet voor: dat blijkt goed gevuld bij leveranciers en slecht bij klanten, en een groot deel van de klanten zit buiten de EU en heeft er geen.

Wat wel werkt is het veld `search_name` in `cashweb.relation`. Dat is bij 100 procent van de klanten met omzet ingevuld en is al een genormaliseerde vorm van de bedrijfsnaam.

Daarom eerst een koppeltabel bouwen, en de KPI daar bovenop.

## Deel A. De koppeltabel

Bouw dit als view of materialized table, en ververs mee met de Cashweb-sync.

```sql
CREATE OR REPLACE VIEW klant_koppeling_lob AS
SELECT
    k.sleutel,
    MAX(k.naam)                                        AS klantnaam,
    MAX(CASE WHEN k.admin_code = 'alaw' THEN k.rn END) AS awc_klantnr,
    MAX(CASE WHEN k.admin_code = 'pgl1' THEN k.rn END) AS afc_klantnr,
    MAX(CASE WHEN k.admin_code = 'acco' THEN k.rn END) AS acc_klantnr,
    COUNT(DISTINCT k.admin_code)                       AS aantal_lob,
    MAX(k.land)                                        AS land,
    CASE
        WHEN k.sleutel IN ('DISTILLERS','DUTCH','GOOD','HOXTON','MAX','SPIRITS')
            THEN 'afgekeurd'
        WHEN k.sleutel IN ('ALFA','COMPAGNIA','DASH','ESSPO','RIGHT','TECAN')
            THEN 'concern'
        WHEN COUNT(DISTINCT k.admin_code) = 1 THEN 'enkel'
        WHEN COUNT(DISTINCT k.admin_code) = 3 THEN 'zeker'
        WHEN LENGTH(k.sleutel) < 6            THEN 'controleren'
        ELSE 'waarschijnlijk'
    END                                                AS zekerheid
FROM (
    SELECT
        r.admin_code,
        TRIM(r.relation_number) AS rn,
        r.name                  AS naam,
        r.country_code          AS land,
        UPPER(REGEXP_REPLACE(TRIM(r.search_name), '[^A-Za-z0-9]', '', 'g')) AS sleutel
    FROM cashweb.relation r
    JOIN (
        SELECT DISTINCT admin_code, TRIM(relation_number) AS rn
        FROM cashweb.ledger_mutations
        WHERE admin_code IN ('alaw','acco','pgl1')
          AND LEFT(account_number, 2) = '12'
          AND book_year IN ('2024','2025')
          AND NULLIF(TRIM(relation_number), '') IS NOT NULL
    ) o
      ON o.admin_code = r.admin_code
     AND o.rn = TRIM(r.relation_number)
    WHERE NULLIF(TRIM(r.search_name), '') IS NOT NULL
) k
GROUP BY k.sleutel;
```

Twee dingen om te weten bij deze query:

- Alleen relaties die als debiteur zijn geboekt tellen mee, dus klanten met echte omzet. Het relatienummer staat namelijk alleen op de balansrekeningen (12xx), niet op de omzetrekeningen. Zonder dit filter zouden leveranciers en lege adresrecords meetellen.
- De zekerheidskolom komt deels uit handmatige controle. De twee lijsten met sleutels zijn nagelopen door AWC: de eerste zijn matches die fout bleken, de tweede zijn hetzelfde concern via een andere entiteit of ander land.

## Deel B. De KPI, met een schakelaar

Er ligt nog een besluit bij het management: telt een concern dat via meerdere landen bij ons koopt als één klant of als meerdere? Bouw dat als instelling, dan hoeft dat besluit niet vooraf te vallen.

```sql
SELECT
    COUNT(*)                                           AS klanten_totaal,
    COUNT(*) FILTER (WHERE aantal_lob = 3)             AS in_alle_drie,
    ROUND(100.0 * COUNT(*) FILTER (WHERE aantal_lob = 3)
          / NULLIF(COUNT(*), 0), 1)                    AS pct_triple_lob
FROM klant_koppeling_lob
WHERE zekerheid <> 'afgekeurd'
  -- concern niet meetellen: zet deze regel aan
  -- AND zekerheid <> 'concern'
;
```

Met concerns meegeteld komt de KPI hoger uit dan zonder. Toon bij voorkeur beide, of maak er een toggle van.

## Deel C. Validatiequery

Gebruik deze om te controleren of jullie bouw dezelfde verdeling geeft als de onze. Draai hem naast jullie eigen tegel.

```sql
SELECT
    zekerheid,
    aantal_lob,
    COUNT(*) AS klanten
FROM klant_koppeling_lob
GROUP BY zekerheid, aantal_lob
ORDER BY zekerheid, aantal_lob;
```

Onze uitkomst op 21 augustus 2026, over boekjaren 2024 en 2025, in totaal 731 klanten:

| zekerheid | aantal_lob | klanten |
|---|---|---|
| enkel | 1 | 468 |
| zeker | 3 | 54 |
| waarschijnlijk | 2 | 107 |
| controleren | 2 | 90 |
| concern | 3 | 6 |
| afgekeurd | 3 | 6 |

Wijken jullie aantallen af, dan is dat waarschijnlijk geen bouwfout. Er wordt aan onze kant nog opgeschoond en er komen boekingen bij. Draai de validatiequery en vergelijk de verdeling, niet het exacte getal. Als de verhouding klopt, klopt de logica.

## Deel D. Werklijst

De categorie `controleren` bevat 90 klanten die bij twee onderdelen voorkomen en een korte sleutel hebben. Daar zit het grootste risico op een valse match, precies zoals bij de zes afgekeurde gevallen. Die lijst wordt aan onze kant nagelopen. De tegel werkt ondertussen gewoon door.

```sql
SELECT sleutel, klantnaam, awc_klantnr, afc_klantnr, acc_klantnr, land
FROM klant_koppeling_lob
WHERE zekerheid = 'controleren'
ORDER BY sleutel;
```

## Onderhoud

Blijkt een match fout, dan zetten wij de sleutel bij de afgekeurde lijst. Blijkt het een concern, dan bij de concernlijst. De tegel hoeft daar niet voor herbouwd te worden.

Op termijn kan deze koppeling ook uit HubSpot komen, zodra daar debiteurnummers voor alle drie de entiteiten staan. Nu bestaat alleen een veld voor AFC. De tegel merkt niets van die overstap, want die leest alleen de koppeltabel.

## Nog niet in deze briefing

Churn ICP. De ICP-regel staat vast (een bedrijf is ICP bij minimaal 3 van de 6 kenmerken), maar het opzegmoment nog niet. Dat wordt bij AWC vastgelegd via een cancellation form en dat veld staat nog niet in de data. Zodra dat rond is volgt deel 3.
