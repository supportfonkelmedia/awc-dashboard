/** Human-readable drill table headers (Overdracht kolomnamen). */
const LABELS = {
    periode: 'Periode',
    waarde: 'Waarde',
    status: 'Status',
    serie: 'Serie',
    scope: 'Scope',
    component: 'Component',
    bedrag: 'Bedrag',
    klanten: 'Klanten',
    kpi_code: 'KPI-code',
    scope_code: 'Scope',
    controle: 'Controle',
    norm: 'Norm',
    toelichting: 'Toelichting',
    naam: 'Naam',
    eigenaar: 'Eigenaar',
    updatefrequentie: 'Update',
    pipeline: 'Pijplijn',
    fase: 'Fase',
    klant: 'Klant',
    verschil: 'Verschil',
    omzet_vorig: 'Omzet vorig',
    omzet_nu: 'Omzet nu',
    notitie: 'Notitie',
    // Detail-drills (kpi_churn_klant, kpi_winrate_deal)
    tegelvenster: 'Venster',
    vertrekdatum: 'Vertrokken op',
    kwartaal: 'Kwartaal',
    vertrekken_die_dag: 'Vertrekken die dag',
    bulkdag: 'Bulkdag',
    icp_score: 'ICP (van 5)',
    nu_weer_klant: 'Nu weer klant',
    deal: 'Deal',
    uitkomst: 'Uitkomst',
    aangemaakt: 'Aangemaakt',
    beslisdatum: 'Beslist op',
    beslissingen_die_dag: 'Beslissingen die dag',
    // Maandviews
    maand: 'Maand',
    entiteit: 'Entiteit',
    admin_code: 'Administratie',
    scope_label: 'Entiteit',
    omzet: 'Omzet',
    inkoop: 'Inkoop',
    bruto_marge: 'Bruto marge',
    loonkosten: 'Loonkosten',
    ratio_maand: 'Ratio maand',
    ebitda: 'EBITDA',
    ebitda_marge_pct: 'EBITDA-marge %',
    ebitda_12m: 'EBITDA 12 mnd',
    ebitda_jaar_tot_nu: 'EBITDA jaar tot nu',
    groep: 'Kostengroep',
    afgesloten: 'Afgesloten',
    gewonnen: 'Gewonnen',
    verloren: 'Verloren',
    aangemaakt_in_maand: 'Aangemaakt',
    peildatum: 'Peildatum',
    soort: 'Soort',
    vertrokken: 'Vertrokken',
    waarvan_bulk: 'Waarvan bulk',
    lopend_kwartaal: 'Lopend kwartaal',
    lopende_maand: 'Lopende maand',
    inbounds: 'Inbounds',
    inbounds_met_verplaatsing: 'Met verplaatsing',
    outbound_zendingen: 'Zendingen',
    outbound_orders: 'Uitgeleverde orders',
};

/** Columns that are plumbing, not information: never shown in the drawer. */
const VERBORGEN = new Set(['_pq_materialized_at', 'company_id', 'deal_id', 'laatst_gesynct', 'geschreven_op']);

/** Readable titles per drill view (the raw view name stays available as a tooltip). */
const VIEW_TITELS = {
    kpi_bm_maand: 'Bruto marge en loonkosten per maand',
    kpi_ebitda_maand: 'EBITDA per maand',
    kpi_kosten_maand: 'Kosten per groep per maand',
    kpi_omzetbrug: 'Omzetbrug',
    kpi_omzetbrug_top: 'Grootste stijgers en dalers',
    kpi_omzetbrug_klant: 'Omzet per klant',
    kpi_triple_lob_maand: 'Triple LOB per maand',
    kpi_triple_lob_te_controleren: 'Nieuwe matches om te controleren',
    kpi_winrate_maand: 'Winrate per peildatum',
    kpi_winrate_fases: 'Fases en uitkomst',
    kpi_winrate_deal: 'Deals',
    kpi_churn_kwartaal: 'Vertrek per kwartaal',
    kpi_churn_klant: 'Vertrokken klanten',
    kpi_acc_dossiers_maand: 'Dossiers per maand',
    kpi_acc_doorlooptijd_maand: 'Doorlooptijd per maand',
    kpi_onboarding_kwartaal: 'Onboarding per kwartaal',
    kpi_d2s_maand: 'Dock-to-stock per maand',
    kpi_awc_ops_maand: 'Inslag en uitslag per maand',
    kpi_awc_schade_klant: 'Schade per klant',
    kpi_afc_sprinter_maand: 'Zendingen per maand',
    kpi_afc_offerte_maand: 'Offertes per maand',
    kpi_handmatig: 'Handmatige invoer',
    kpi_registry: 'KPI-register',
    kpi_controles: 'Datacontroles',
};

/**
 * @param {string} field
 */
export function drillColumnHeader(field) {
    return LABELS[field] ?? field.replace(/_/g, ' ');
}

/**
 * @param {string} view
 */
export function drillViewTitel(view) {
    return VIEW_TITELS[view] ?? view.replace(/^kpi_/, '').replace(/_/g, ' ');
}

/**
 * Columns to show for a set of rows, without plumbing columns. `scope_code` is dropped when
 * every row has the same value (the drawer already filtered on it).
 *
 * @param {Array<Record<string, unknown>>} rows
 */
export function drillKolommen(rows) {
    if (!rows?.length) {
        return [];
    }
    const eenScope = new Set(rows.map((r) => r.scope_code ?? '')).size <= 1;

    return Object.keys(rows[0]).filter(
        (k) => !VERBORGEN.has(k) && !(k === 'scope_code' && eenScope),
    );
}

const ISO_DATUM = /^(\d{4})-(\d{2})-(\d{2})(?:[T ][\d:.]+(?:Z|[+-]\d{2}:?\d{2})?)?$/;
const getal = new Intl.NumberFormat('nl-NL', { maximumFractionDigits: 2 });

/**
 * Display value for one drill cell: Ja/Nee for booleans, nl-NL numbers, dd-mm-jjjj dates.
 *
 * @param {unknown} value
 */
export function drillWaarde(value) {
    if (value === null || value === undefined || value === '') {
        return '';
    }
    if (typeof value === 'boolean') {
        return value ? 'Ja' : 'Nee';
    }
    if (typeof value === 'number') {
        return getal.format(value);
    }
    const s = String(value);
    const m = s.match(ISO_DATUM);
    if (m) {
        return `${m[3]}-${m[2]}-${m[1]}`;
    }

    return s;
}
