-- Peliqan "My Queries".kpi_afc_resultaat_maand_my_queries (table_id 1579285), live stand 2026-11-13 (vorige stand: git-historie)
-- AFC-analyse (awc-dashboard /kpi/afc/analyse) | resultaat volgens Cash per maand (pgl1).
-- Sinds 2026-11-13 op de grootboekperiode (book_period_ledger), net als kpi_bm_maand / kpi_ebitda_maand.
-- Daarvoor las deze view afc_control_center.afc_resultaat_maand (Floor), die de documentperiode volgt en
-- terugkerende boekingen (zelfde inhoud, verspreid over 12 grootboekperiodes) wegfiltert als dubbel.
-- Rekeningindeling gelijk aan die van Floor: 8xxx omzet, 6xxx kostprijs (6021 Sim Cargo, 6010/6050 SVZ),
-- 4xxx bedrijfskosten, 9000 resultaat Humber, 9100 vennootschapsbelasting; VERK 2001 invoerrechten
-- doorbelast, VERK 1560 btw verkoop. Omzet en resultaat positief = winst.
-- periode_afwijkend = aantal regels waarvan de documentperiode afwijkt van de grootboekperiode.
with m as (
  select
    cast(book_year as int) as boekjaar,
    least(greatest(cast(right(book_period_ledger, 2) as int), 1), 12) as mnd,
    trim(journal_code) as dagboek,
    trim(account_number) as rekening,
    cast(replace(amount, ',', '.') as numeric) as bedrag,
    (book_period <> book_period_ledger) as afwijkend
  from cashweb.ledger_mutations
  where admin_code = 'pgl1'
    and length(book_period_ledger) = 4
    and amount is not null and amount <> ''
    and (left(account_number, 1) in ('4', '6', '8')
         or trim(account_number) in ('9000', '9100')
         or (trim(journal_code) = 'VERK' and trim(account_number) in ('1560', '2001')))
),
a as (
  select boekjaar, mnd,
    sum(case when rekening like '8%' then -bedrag else 0 end) as omzet,
    sum(case when dagboek = 'VERK' and rekening = '2001' then -bedrag else 0 end) as invoerrechten_doorbelast,
    sum(case when dagboek = 'VERK' and rekening = '1560' then -bedrag else 0 end) as btw_verkoop,
    sum(case when rekening like '6%' then bedrag else 0 end) as kostprijs,
    sum(case when rekening = '6021' then bedrag else 0 end) as kostprijs_sim_cargo,
    sum(case when rekening in ('6010', '6050') then bedrag else 0 end) as kostprijs_svz,
    sum(case when rekening like '4%' then bedrag else 0 end) as bedrijfskosten,
    sum(case when rekening = '9000' then -bedrag else 0 end) as resultaat_humber,
    sum(case when rekening = '9100' then bedrag else 0 end) as vennootschapsbelasting,
    sum(case when afwijkend then 1 else 0 end) as periode_afwijkend
  from m
  group by 1, 2
)
select
  boekjaar * 100 + mnd as periode_id,
  boekjaar,
  mnd as maandnummer,
  make_date(boekjaar, mnd, 1) as maand,
  round(omzet, 2) as omzet,
  round(invoerrechten_doorbelast, 2) as invoerrechten_doorbelast,
  round(omzet + invoerrechten_doorbelast, 2) as omzet_incl_invoerrechten,
  round(btw_verkoop, 2) as btw_verkoop,
  round(kostprijs, 2) as kostprijs,
  round(kostprijs_sim_cargo, 2) as kostprijs_sim_cargo,
  round(kostprijs_svz, 2) as kostprijs_svz,
  round(omzet - kostprijs, 2) as brutomarge,
  case when omzet <> 0 then round(100 * (omzet - kostprijs) / omzet, 1) end as brutomarge_pct,
  round(bedrijfskosten, 2) as bedrijfskosten,
  round(resultaat_humber, 2) as resultaat_humber,
  round(omzet - kostprijs - bedrijfskosten + resultaat_humber, 2) as resultaat_voor_belasting,
  round(vennootschapsbelasting, 2) as vennootschapsbelasting,
  round(omzet - kostprijs - bedrijfskosten + resultaat_humber - vennootschapsbelasting, 2) as resultaat_na_belasting,
  periode_afwijkend
from a
where make_date(boekjaar, mnd, 1) <= cast(date_trunc('month', current_date) as date)
