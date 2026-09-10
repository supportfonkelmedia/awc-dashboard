# Bouwbriefing KPI-dashboard AWC, deel 3: Dock-to-Stock

Dock-to-Stock meet hoe snel binnengekomen goederen in het magazijn liggen: van lossen tot verwerkt in voorraad. Norm: binnen 24 uur. Dit is een operationele tegel voor AWC (warehouse), geen MT-KPI. Hij vervangt de huidige "Dock-to-Stock: Niet gemeten"-tegel.

Alle data komt uit de 7T-database (SQL Server), schema `dbo`. Net als bij deel 2 staat onderaan een validatiequery: geeft jullie tegel dezelfde uitkomst, dan staat de bouw goed.

---

## De rekenregel

Per inbound-order:

- **Start**: het losmoment. Veld `Los_Datum` op `Spare_Orders`.
- **Einde**: het moment dat de voorraadverplaatsing is verwerkt. De eerste regel in `Voorraad_Verplaatsingen` met `Status = 30` (dat heet "Verwerkt door 7T"), veld `MutatieDatum`.
- **Doorlooptijd** = einde min start, in uren.
- **KPI** = percentage orders met doorlooptijd van 24 uur of minder.

## Tabellen en koppeling

1. `Spare_Orders` (de inbound-order). Filter: `Gelost = 1` en `Los_Datum` in de gekozen periode.
2. `Ontvangsten` (de ontvangst). Koppel: `LTRIM(RTRIM(Ontvangsten.Spare_Order_ID)) = LTRIM(RTRIM(Spare_Orders.ID))`. Let op de LTRIM/RTRIM, de ID's bevatten spaties.
3. `Voorraad_Verplaatsingen` (de inslag). Koppel: `Voorraad_Verplaatsingen.Ontvangst_ID = Ontvangsten.ID`, filter `Status = 30`. Neem per order de vroegste `MutatieDatum`.

## De dekking, en waarom die erbij moet

Niet elke inbound krijgt een voorraadverplaatsing. Stand begin september over 2026: 11.125 geloste orders, waarvan 6.776 met een verplaatsing (61 procent) en 4.329 zonder. Die tweede groep heeft wel een afgeronde ontvangst maar nooit een verplaatsingsregel. Dat is één consistente stroom het hele jaar door, geen registratiefout. Waarschijnlijk goederen die administratief van eigenaar wisselen of niet fysiek ingeslagen hoeven te worden; de bevestiging daarvan ligt bij AWC (Edo).

Bouw de tegel daarom zo:

- Bereken de KPI alleen over orders mét een status-30-verplaatsing.
- Toon de dekking in de tegel, bijvoorbeeld: "gemeten over 61% van de inbounds".
- Maak de populatie niet hard in code. Als AWC straks bevestigt wat de andere 39 procent is, kan de definitie een instelling zijn in plaats van een herbouw.

## Presentatie-afspraken

- **Gebruik de mediaan als je een doorlooptijd toont**, niet het gemiddelde. Er zitten uitschieters tot 68 dagen tussen die het gemiddelde omhoog trekken.
- **Markeer de lopende maand als voorlopig.** Trage orders van die maand zijn nog niet afgerond, dus het maandcijfer ziet er eerst te mooi uit en daalt daarna nog.
- Trendgrafiek per maand erbij, zoals bij alle KPI's afgesproken.

## Controlecijfers (stand 3 september 2026, heel 2026)

- Meetbare orders (met status-30-verplaatsing): 6.765
- Binnen 24 uur: 5.049, oftewel 74,6 procent
- Gemiddelde doorlooptijd: 25 uur

Deze cijfers schuiven mee met de data. Draai daarom de validatiequery hieronder op het moment van bouwen en vergelijk met jullie tegel.

## Validatiequery

```sql
SELECT
  COUNT(*) AS orders,
  SUM(CASE WHEN DATEDIFF(hour, x.los, x.klaar) <= 24 THEN 1 ELSE 0 END) AS binnen_24u,
  CAST(100.0 * SUM(CASE WHEN DATEDIFF(hour, x.los, x.klaar) <= 24 THEN 1 ELSE 0 END)
       / COUNT(*) AS numeric(5,1)) AS pct_binnen_24u
FROM (
  SELECT LTRIM(RTRIM(s.ID)) AS sid, s.Los_Datum AS los, MIN(vv.MutatieDatum) AS klaar
  FROM dbo.Spare_Orders s
  JOIN dbo.Ontvangsten o
    ON LTRIM(RTRIM(o.Spare_Order_ID)) = LTRIM(RTRIM(s.ID))
  JOIN dbo.Voorraad_Verplaatsingen vv
    ON vv.Ontvangst_ID = o.ID AND vv.Status = 30
  WHERE s.Los_Datum >= '2026-01-01' AND s.Gelost = 1
  GROUP BY LTRIM(RTRIM(s.ID)), s.Los_Datum
) x
```

## Bijlage: de statussen zoals ze echt gebruikt worden

De statustabellen in 7T bevatten veel meer statussen dan er in de praktijk voorkomen. Dit is wat er bij de 2026-inbounds echt wordt gebruikt, zodat jullie niet zelf hoeven te puzzelen.

**Spare_Orders** (soort `Spare`):

| Status | Naam | Betekenis voor de bouw |
|---|---|---|
| 25 | Controleren | Nog in behandeling, valt buiten de meting |
| 27 | Gereed voor controle | Nog in behandeling, valt buiten de meting |
| 30 | Afgerond | De normale eindstand, vrijwel alle orders |

**Ontvangsten** (soort `Ontv`): in de praktijk staat alles op status 80, "Ontvangst afgerond". De tussenstatussen (45 t/m 78) kom je als eindstand niet tegen.

**Voorraad_Verplaatsingen** (soort `VrdV`):

| Status | Naam | Betekenis voor de bouw |
|---|---|---|
| 5 | Invoer verplaatsing | Onderweg, telt nog niet als klaar |
| 25 | Vrij voor verplaatsing | Onderweg, telt nog niet als klaar |
| 30 | Verwerkt door 7T | Het eindmoment van de KPI |

99,8 procent van de verplaatsingen bereikt status 30, dus dat eindpunt is betrouwbaar. Status 27 ("Verplaatsing geregistreerd") bestaat in de definitie maar wordt nooit gebruikt; niet op bouwen. Het dynamisch magazijn (status 10 en 20) wordt ook niet gebruikt.

---
