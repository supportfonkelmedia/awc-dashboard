-- Peliqan "My Queries".kpi_controles (table_id 1418985), stand 2026-11-12
WITH vm AS (
  SELECT
    CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '1 MONTH' AS DATE) AS vorige_maand
), vers AS (
  SELECT
    'Cashweb' AS bron,
    MAX(_sdc_batched_at) AS laatst
  FROM cashweb.ledger_balances
  UNION ALL
  SELECT
    'HubSpot' AS literal,
    MAX(_sdc_batched_at) AS max_Sdc_Batched_At
  FROM hubspot_v2.deals
  UNION ALL
  SELECT
    'Sprinter3000' AS literal,
    MAX(_sdc_batched_at) AS max_Sdc_Batched_At
  FROM sprinter_api.shipments
  UNION ALL
  SELECT
    '7T dock-to-stock (nachtapp)' AS literal,
    MAX(geschreven_op) AS maxGeschreven_Op
  FROM kpi_data.dock_to_stock_maand
  UNION ALL
  SELECT
    '7T schade en throughput (nachtapp)' AS literal,
    MAX(geschreven_op) AS maxGeschreven_Op
  FROM kpi_data.awc_operatie_maand
), c_vers AS (
  SELECT
    1 AS volgorde,
    'versheid' AS soort,
    'Versheid ' || bron AS controle,
    bron,
    ROUND(CAST(EXTRACT(EPOCH FROM (
      CURRENT_TIMESTAMP - laatst
    )) / 3600 AS DECIMAL), 1) AS waarde,
    'uren sinds laatste sync, norm 36' AS norm,
    CASE
      WHEN laatst IS NULL
      THEN 'fout'
      WHEN CURRENT_TIMESTAMP - laatst <= INTERVAL '36 HOURS'
      THEN 'ok'
      WHEN CURRENT_TIMESTAMP - laatst <= INTERVAL '72 HOURS'
      THEN 'let_op'
      ELSE 'fout'
    END AS status,
    'Laatste sync ' || TO_CHAR(laatst AT TIME ZONE 'Europe/Amsterdam', 'DD-MM-YYYY HH24:MI') AS toelichting
  FROM vers
), vers_data AS (
  SELECT
    'HubSpot' AS bron,
    'Versheid HubSpot tickets' AS controle,
    'uren sinds laatste ticket in de data, norm 48 (zondag en maandag 96)' AS norm,
    'Gemeten op de data zelf: laatste ticket aangemaakt of gewijzigd op ' AS uitleg_voor,
    '. Churn, onboarding en de twee ACC-KPI''s lezen tickets. Staat dit stil, dan haalt de koppeling niets nieuws meer op.' AS uitleg_na,
    MAX(GREATEST(createdate, hs_lastmodifieddate)) AS laatst,
    48 AS ok_uren,
    96 AS ok_uren_weekend,
    120 AS let_op_uren
  FROM hubspot_v2.tickets
  WHERE
    GREATEST(createdate, hs_lastmodifieddate) <= CURRENT_TIMESTAMP + INTERVAL '1 HOUR'
  UNION ALL
  SELECT
    'HubSpot' AS bron,
    'Versheid HubSpot bedrijven' AS controle,
    'uren sinds laatste bedrijf in de data, norm 48 (zondag en maandag 96)' AS norm,
    'Gemeten op de data zelf: laatste bedrijf aangemaakt of gewijzigd op ' AS uitleg_voor,
    '. Churn leest bedrijven. Staat dit stil, dan haalt de koppeling niets nieuws meer op.' AS uitleg_na,
    MAX(GREATEST(createdate, hs_lastmodifieddate)) AS laatst,
    48 AS ok_uren,
    96 AS ok_uren_weekend,
    120 AS let_op_uren
  FROM hubspot_v2.companies
  WHERE
    GREATEST(createdate, hs_lastmodifieddate) <= CURRENT_TIMESTAMP + INTERVAL '1 HOUR'
  UNION ALL
  SELECT
    'Sprinter3000' AS bron,
    'Versheid Sprinter3000 zendingen' AS controle,
    'uren sinds laatste zending in de data, norm 48 (zondag en maandag 96)' AS norm,
    'Gemeten op de data zelf: laatste zending aangemaakt of gerapporteerd op ' AS uitleg_voor,
    '. De Sprinter-sync draait dagelijks om 02:30 UTC. Staat dit stil, dan mist de AFC-tegel recente zendingen.' AS uitleg_na,
    MAX(GREATEST(create_date, report_date)) AS laatst,
    48 AS ok_uren,
    96 AS ok_uren_weekend,
    120 AS let_op_uren
  FROM sprinter_api.shipments
  WHERE
    GREATEST(create_date, report_date) <= CURRENT_TIMESTAMP + INTERVAL '1 HOUR'
  UNION ALL
  SELECT
    'Cashweb' AS bron,
    'Versheid Cashweb mutaties' AS controle,
    'uren sinds laatste binnengekomen boekingsregels, norm 96' AS norm,
    'Laatste nieuwe of gewijzigde boekingsregels binnengekomen op ' AS uitleg_voor,
    '. De financiële KPI''s lezen deze mutaties. Komt er langer dan een week niets binnen, dan staat de koppeling of de boekhouding stil.' AS uitleg_na,
    MAX(_sdc_batched_at) AS laatst,
    96 AS ok_uren,
    96 AS ok_uren_weekend,
    168 AS let_op_uren
  FROM cashweb.ledger_mutations
), c_vers_data AS (
  SELECT
    1 AS volgorde,
    'versheid' AS soort,
    controle,
    bron,
    ROUND(CAST(EXTRACT(EPOCH FROM (
      CURRENT_TIMESTAMP - laatst
    )) / 3600 AS DECIMAL), 1) AS waarde,
    norm,
    CASE
      WHEN laatst IS NULL
      THEN 'fout'
      WHEN CURRENT_TIMESTAMP - laatst <= ok_uren * INTERVAL '1 HOUR'
      THEN 'ok'
      WHEN CURRENT_TIMESTAMP - laatst <= ok_uren_weekend * INTERVAL '1 HOUR'
      AND EXTRACT(ISODOW FROM CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Amsterdam') IN (7, 1)
      THEN 'ok'
      WHEN CURRENT_TIMESTAMP - laatst <= let_op_uren * INTERVAL '1 HOUR'
      THEN 'let_op'
      ELSE 'fout'
    END AS status,
    uitleg_voor || COALESCE(TO_CHAR(laatst AT TIME ZONE 'Europe/Amsterdam', 'DD-MM-YYYY HH24:MI'), 'onbekend') || uitleg_na AS toelichting
  FROM vers_data
), spr AS (
  SELECT
    CAST(DATE_TRUNC('MONTH', report_date) AS DATE) AS maand,
    COUNT(*) AS n
  FROM sprinter_api.shipments
  WHERE
    report_date >= CURRENT_DATE - INTERVAL '8 MONTHS'
    AND COALESCE(shipment_status_code, '') <> 'C'
  GROUP BY
    1
), acc AS (
  SELECT
    maand,
    SUM(dossiers) AS n
  FROM "My Queries".kpi_acc_dossiers_maand
  GROUP BY
    1
), d2s AS (
  SELECT
    maand,
    inbounds AS n
  FROM kpi_data.dock_to_stock_maand
), manco AS (
  SELECT
    maand,
    beschadigd_geleverd + beschadigd_awc + niet_geleverd + artikelinfo_onjuist AS n
  FROM kpi_data.awc_operatie_maand
), vol AS (
  SELECT
    'Sprinter3000' AS bron,
    'zendingen' AS wat,
    maand,
    n
  FROM spr
  UNION ALL
  SELECT
    'HubSpot (Customs Pipeline)' AS literal,
    'dossiers' AS literal,
    maand,
    n
  FROM acc
  UNION ALL
  SELECT
    '7T' AS literal,
    'geloste inbounds' AS literal,
    maand,
    n
  FROM d2s
  UNION ALL
  SELECT
    '7T manco-registratie' AS literal,
    'orders met een manco' AS literal,
    maand,
    n
  FROM manco
), c_vol AS (
  SELECT
    2 AS volgorde,
    'volume' AS soort,
    'Volume ' || v.bron AS controle,
    v.bron,
    CAST(MAX(CASE WHEN v.maand = vm.vorige_maand THEN v.n END) AS DECIMAL) AS waarde,
    'aantal ' || MIN(v.wat) || ' vorige maand, norm minimaal 50% van gemiddelde ' || ROUND(
      AVG(
        CASE
          WHEN v.maand BETWEEN vm.vorige_maand - INTERVAL '3 MONTHS' AND vm.vorige_maand - INTERVAL '1 MONTH'
          THEN v.n
        END
      )
    ) AS norm,
    CASE
      WHEN MAX(CASE WHEN v.maand = vm.vorige_maand THEN v.n END) IS NULL
      THEN 'fout'
      WHEN MAX(CASE WHEN v.maand = vm.vorige_maand THEN v.n END) >= 0.5 * AVG(
        CASE
          WHEN v.maand BETWEEN vm.vorige_maand - INTERVAL '3 MONTHS' AND vm.vorige_maand - INTERVAL '1 MONTH'
          THEN v.n
        END
      )
      THEN 'ok'
      ELSE 'fout'
    END AS status,
    'Vorige maand tegenover het gemiddelde van de drie maanden daarvoor. Een val onder de helft wijst meestal op een koppeling die niet alles ophaalt, of een registratie die stil is gevallen.' AS toelichting
  FROM vol AS v
  CROSS JOIN vm
  GROUP BY
    v.bron
), brug AS (
  SELECT
    bedrag,
    stand_per
  FROM "My Queries".kpi_omzetbrug
  WHERE
    scope = 'Concern' AND component = 'eind'
), gb AS (
  SELECT
    SUM(l.omzet) AS omzet
  FROM "My Queries".kpi_omzet_lob AS l
  CROSS JOIN brug AS b
  WHERE
    l.scope_code = 'concern'
    AND l.maand > b.stand_per - INTERVAL '12 MONTHS'
    AND l.maand <= b.stand_per
), c_aansl AS (
  SELECT
    3 AS volgorde,
    'aansluiting' AS soort,
    'Omzetbrug tegenover grootboek' AS controle,
    'Cashweb' AS bron,
    ROUND(100.0 * (
      gb.omzet - brug.bedrag
    ) / NULLIF(gb.omzet, 0), 2) AS waarde,
    'procent verschil, norm tussen 0 en 3 (intercompany)' AS norm,
    CASE
      WHEN (
        gb.omzet - brug.bedrag
      ) / NULLIF(gb.omzet, 0) BETWEEN 0 AND 0.03
      THEN 'ok'
      ELSE 'fout'
    END AS status,
    'Grootboek ' || ROUND(gb.omzet) || ', brug ' || ROUND(brug.bedrag) || '. Het verschil hoort gelijk te zijn aan de omzet tussen de eigen entiteiten.' AS toelichting
  FROM gb
  CROSS JOIN brug
), cw AS (
  SELECT
    SUM(ebitda) AS ebitda
  FROM "My Queries".kpi_ebitda_maand
  WHERE
    scope_code = 'concern'
    AND maand >= CAST('2025-01-01' AS DATE)
    AND maand < CAST('2026-01-01' AS DATE)
), sar AS (
  SELECT
    waarde
  FROM "My Queries".kpi_handmatig
  WHERE
    kpi_code = 'ebitda'
    AND scope_code = 'concern'
    AND periode_einde = CAST('2025-12-31' AS DATE)
), c_sar AS (
  SELECT
    3 AS volgorde,
    'aansluiting' AS soort,
    'EBITDA Cashweb tegenover SAR-waardering (boekjaar 2025)' AS controle,
    'Cashweb' AS bron,
    ROUND(100.0 * (
      cw.ebitda - sar.waarde
    ) / NULLIF(sar.waarde, 0), 2) AS waarde,
    'procent verschil, norm binnen 2' AS norm,
    CASE
      WHEN ABS((
        cw.ebitda - sar.waarde
      ) / NULLIF(sar.waarde, 0)) <= 0.02
      THEN 'ok'
      WHEN ABS((
        cw.ebitda - sar.waarde
      ) / NULLIF(sar.waarde, 0)) <= 0.05
      THEN 'let_op'
      ELSE 'fout'
    END AS status,
    'Cashweb ' || ROUND(cw.ebitda) || ', SAR ' || ROUND(sar.waarde) || '. De SAR-cijfers komen uit de jaarrekening; AFC 2025 is daar nog voorlopig.' AS toelichting
  FROM cw
  CROSS JOIN sar
), kg AS (
  SELECT
    SUM(CASE WHEN groep = '1 Omzet' THEN bedrag ELSE -bedrag END) AS ebitda_uit_groepen
  FROM "My Queries".kpi_kosten_maand
  WHERE
    maand >= CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '13 MONTHS' AS DATE)
    AND maand <= CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '2 MONTHS' AS DATE)
), ke AS (
  SELECT
    SUM(ebitda) AS ebitda
  FROM "My Queries".kpi_ebitda_maand
  WHERE
    scope_code = 'concern'
    AND maand >= CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '13 MONTHS' AS DATE)
    AND maand <= CAST(DATE_TRUNC('MONTH', CURRENT_DATE) - INTERVAL '2 MONTHS' AS DATE)
), c_kg AS (
  SELECT
    3 AS volgorde,
    'aansluiting' AS soort,
    'EBITDA tegenover kostengroepen (laatste 12 maanden)' AS controle,
    'Cashweb' AS bron,
    ROUND(ABS(ke.ebitda - kg.ebitda_uit_groepen)) AS waarde,
    'euro verschil, norm onder 1.000' AS norm,
    CASE WHEN ABS(ke.ebitda - kg.ebitda_uit_groepen) < 1000 THEN 'ok' ELSE 'fout' END AS status,
    'EBITDA ' || ROUND(ke.ebitda) || ', som van omzet min kostengroepen ' || ROUND(kg.ebitda_uit_groepen) || '. Een verschil betekent dat een rekening in de ene view wel en in de andere niet meetelt.' AS toelichting
  FROM ke
  CROSS JOIN kg
), c_d2s AS (
  SELECT
    4 AS volgorde,
    'dekking' AS soort,
    'Dekking dock-to-stock' AS controle,
    '7T' AS bron,
    d.pct_met_verplaatsing AS waarde,
    'procent inbounds met verplaatsing, norm 55 tot 70' AS norm,
    CASE
      WHEN d.pct_met_verplaatsing BETWEEN 55 AND 70
      THEN 'ok'
      WHEN d.pct_met_verplaatsing BETWEEN 45 AND 80
      THEN 'let_op'
      ELSE 'fout'
    END AS status,
    'Maand ' || TO_CHAR(d.maand, 'MM-YYYY') || '. Buiten de band betekent dat de meting over een andere groep inbounds gaat dan normaal.' AS toelichting
  FROM kpi_data.dock_to_stock_maand AS d
  CROSS JOIN vm
  WHERE
    d.maand = vm.vorige_maand
), c_tlob AS (
  SELECT
    5 AS volgorde,
    'werklijst' AS soort,
    'Triple LOB: matches te controleren' AS controle,
    'Cashweb' AS bron,
    CAST(COUNT(*) AS DECIMAL) AS waarde,
    'aantal, norm 0' AS norm,
    CASE WHEN COUNT(*) = 0 THEN 'ok' ELSE 'let_op' END AS status,
    'Nieuwe klanten die bij alle drie de entiteiten lijken voor te komen en nog beoordeeld moeten worden in kpi_triple_lob_beoordeling.' AS toelichting
  FROM "My Queries".kpi_triple_lob_te_controleren
)
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS gecontroleerd_op
FROM c_vers
UNION ALL
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS currenttimestamp
FROM c_vers_data
UNION ALL
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS currenttimestamp
FROM c_vol
UNION ALL
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS currenttimestamp
FROM c_aansl
UNION ALL
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS currenttimestamp
FROM c_sar
UNION ALL
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS currenttimestamp
FROM c_kg
UNION ALL
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS currenttimestamp
FROM c_d2s
UNION ALL
SELECT
  volgorde,
  soort,
  controle,
  bron,
  waarde,
  norm,
  status,
  toelichting,
  CURRENT_TIMESTAMP AS currenttimestamp
FROM c_tlob
