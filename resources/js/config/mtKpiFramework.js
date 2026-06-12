/**
 * MT KPI framework — aligned with AWC KPI Structuur (Excel).
 * Status: live | in_development | not_measured | to_define
 */

export const KPI_STATUS = {
    LIVE: 'live',
    IN_DEVELOPMENT: 'in_development',
    NOT_MEASURED: 'not_measured',
    TO_DEFINE: 'to_define',
};

export const STATUS_LABELS = {
    [KPI_STATUS.LIVE]: 'Live',
    [KPI_STATUS.IN_DEVELOPMENT]: 'In ontwikkeling',
    [KPI_STATUS.NOT_MEASURED]: 'Niet gemeten',
    [KPI_STATUS.TO_DEFINE]: 'Te definiëren',
};

export const STATUS_TAG_SEVERITY = {
    [KPI_STATUS.LIVE]: 'success',
    [KPI_STATUS.IN_DEVELOPMENT]: 'warn',
    [KPI_STATUS.NOT_MEASURED]: 'secondary',
    [KPI_STATUS.TO_DEFINE]: 'info',
};

/** @type {Record<string, { id: string, label: string, theme: string }>} */
export const STRATEGIC_KPIS = {
    ebitda: {
        id: 'ebitda',
        label: 'EBITDA',
        theme: 'Financiële gezondheid',
        defaultStatus: KPI_STATUS.TO_DEFINE,
        source: 'Cashweb',
        note: 'Accountmapping met boekhouding (Frits).',
    },
    ltv_triple_lob: {
        id: 'ltv_triple_lob',
        label: 'Life Time Value (Triple LOB)',
        theme: 'Waarde',
        defaultStatus: KPI_STATUS.IN_DEVELOPMENT,
        source: 'Cashweb · HubSpot',
        note: 'Formule en triple-LOB-validatie nog af te stemmen.',
    },
    ab_players: {
        id: 'ab_players',
        label: 'A/B Players',
        theme: 'Mensen',
        defaultStatus: KPI_STATUS.NOT_MEASURED,
        source: 'Hooray',
        note: 'Nog niet gekoppeld.',
    },
    marge_per_loon: {
        id: 'marge_per_loon',
        label: 'Bruto marge per loonkosten',
        theme: 'Efficiëntie',
        defaultStatus: KPI_STATUS.IN_DEVELOPMENT,
        source: 'Cashweb (SAL-proxy)',
        note: 'Vervanger voor marge per FTE zolang uren ontbreken.',
    },
    revenue_per_lob: {
        id: 'revenue_per_lob',
        label: 'Revenue per Line of Business',
        theme: 'Groei',
        defaultStatus: KPI_STATUS.IN_DEVELOPMENT,
        source: 'Cashweb',
        note: 'Uitsplitsing per sub_administration / entiteit.',
    },
};

export const CUSTOMER_JOURNEY_STAGES = [
    {
        id: 'awareness',
        label: 'Bewustwording',
        kpis: ['icp_interactions'],
    },
    {
        id: 'consideration',
        label: 'Overweging',
        kpis: ['client_requests_lob'],
    },
    {
        id: 'decision',
        label: 'Besluit',
        kpis: ['winrate'],
    },
    {
        id: 'onboarding',
        label: 'Onboarding',
        kpis: ['time_to_onboarding'],
    },
    {
        id: 'adoption',
        label: 'Adoptie',
        kpis: [
            'storage_lead_time',
            'occupancy_rate',
            'on_time_delivery',
        ],
    },
    {
        id: 'retention',
        label: 'Retentie',
        kpis: ['churn', 'tickets', 'margin_per_shipment'],
    },
];

/** @type {Record<string, object>} */
export const OPERATIONAL_KPIS = {
    icp_interactions: {
        id: 'icp_interactions',
        label: 'ICP-interacties',
        strategicLink: 'revenue_per_lob',
        defaultStatus: KPI_STATUS.IN_DEVELOPMENT,
        source: 'HubSpot',
    },
    client_requests_lob: {
        id: 'client_requests_lob',
        label: 'Client requests per LOB',
        strategicLink: 'revenue_per_lob',
        defaultStatus: KPI_STATUS.NOT_MEASURED,
        source: 'HubSpot',
    },
    winrate: {
        id: 'winrate',
        label: 'Winrate',
        strategicLink: 'revenue_per_lob',
        defaultStatus: KPI_STATUS.LIVE,
        source: 'HubSpot',
    },
    time_to_onboarding: {
        id: 'time_to_onboarding',
        label: 'Time to onboarding',
        strategicLink: 'ltv_triple_lob',
        defaultStatus: KPI_STATUS.IN_DEVELOPMENT,
        source: 'HubSpot',
    },
    storage_lead_time: {
        id: 'storage_lead_time',
        label: 'Storage lead time',
        strategicLink: 'marge_per_loon',
        defaultStatus: KPI_STATUS.NOT_MEASURED,
        source: '7T Software',
    },
    occupancy_rate: {
        id: 'occupancy_rate',
        label: 'Bezettingsgraad',
        strategicLink: 'marge_per_loon',
        defaultStatus: KPI_STATUS.NOT_MEASURED,
        source: '7T Software',
    },
    on_time_delivery: {
        id: 'on_time_delivery',
        label: 'On-time delivery',
        strategicLink: 'marge_per_loon',
        defaultStatus: KPI_STATUS.TO_DEFINE,
        source: 'Sprinter3000',
        note: 'Definitie “op tijd” nog vast te leggen.',
    },
    churn: {
        id: 'churn',
        label: 'Churn',
        strategicLink: 'ltv_triple_lob',
        defaultStatus: KPI_STATUS.IN_DEVELOPMENT,
        source: 'HubSpot',
    },
    tickets: {
        id: 'tickets',
        label: 'Tickets',
        strategicLink: 'ltv_triple_lob',
        defaultStatus: KPI_STATUS.LIVE,
        source: 'HubSpot',
    },
    margin_per_shipment: {
        id: 'margin_per_shipment',
        label: 'Marge per zending',
        strategicLink: 'marge_per_loon',
        defaultStatus: KPI_STATUS.LIVE,
        source: 'Sprinter3000',
    },
};

export const TACTICAL_KPIS = [
    {
        id: 'automation_goals',
        label: '% behaalde automatiseringsdoelen',
        strategicLink: 'marge_per_loon',
        defaultStatus: KPI_STATUS.NOT_MEASURED,
        source: '—',
    },
    {
        id: 'triple_lob_pct',
        label: '% Triple LOB',
        strategicLink: 'ltv_triple_lob',
        defaultStatus: KPI_STATUS.IN_DEVELOPMENT,
        source: 'Cashweb',
    },
    {
        id: 'enps',
        label: 'eNPS',
        strategicLink: 'ab_players',
        defaultStatus: KPI_STATUS.NOT_MEASURED,
        source: 'Microsoft Forms',
    },
    {
        id: 'nps',
        label: 'NPS (intern vs. extern)',
        strategicLink: 'ltv_triple_lob',
        defaultStatus: KPI_STATUS.NOT_MEASURED,
        source: 'HubSpot',
    },
];

export const ENTITY_KPIS = {
    AWC: {
        code: 'AWC',
        label: 'AWC — Warehouse',
        routeName: 'awc.dashboard',
        source: '7T Software',
        kpis: [
            {
                id: 'dock_to_stock',
                label: 'Dock-to-Stock',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'perfect_order_rate',
                label: 'Perfect Order Rate',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'inventory_accuracy',
                label: 'Inventory Accuracy',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'otif',
                label: 'OTIF',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'throughput',
                label: 'Throughput',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'damage_rate',
                label: 'Damage Rate',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
        ],
    },
    AFC: {
        code: 'AFC',
        label: 'AFC — Freight',
        routeName: 'afc.dashboard',
        source: 'Sprinter3000',
        kpis: [
            {
                id: 'modal_split',
                label: 'Modal split',
                strategicLink: 'revenue_per_lob',
                defaultStatus: KPI_STATUS.LIVE,
            },
            {
                id: 'quote_conversion',
                label: 'Quote conversion',
                strategicLink: 'revenue_per_lob',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'margin_per_modality',
                label: 'Marge per modaliteit',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.LIVE,
            },
            {
                id: 'shipments_afc',
                label: 'Zendingen',
                strategicLink: 'revenue_per_lob',
                defaultStatus: KPI_STATUS.LIVE,
            },
        ],
    },
    ACC: {
        code: 'ACC',
        label: 'ACC — Customs',
        routeName: 'acc.dashboard',
        source: 'Softpak',
        kpis: [
            {
                id: 'import_export_tickets',
                label: 'Import / export / consult-tickets',
                strategicLink: 'revenue_per_lob',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'dossier_lead_time',
                label: 'Doorlooptijd dossier tot aangifte',
                strategicLink: 'marge_per_loon',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
            {
                id: 'first_time_right',
                label: 'First time right',
                strategicLink: 'ltv_triple_lob',
                defaultStatus: KPI_STATUS.NOT_MEASURED,
            },
        ],
    },
};

export const STRATEGIC_KPI_ORDER = [
    'ebitda',
    'ltv_triple_lob',
    'ab_players',
    'marge_per_loon',
    'revenue_per_lob',
];

/**
 * Per-KPI explanation copy for the info drawer.
 * description = wat meet de KPI · method = hoe wordt het berekend / databron.
 * Keyed by KPI id so we don't have to touch every definition object.
 * @type {Record<string, { description: string, method: string }>}
 */
export const KPI_EXPLAIN = {
    // Strategisch
    ebitda: {
        description:
            'Bedrijfsresultaat vóór rente, belasting, afschrijvingen en amortisatie — kernmaat voor financiële gezondheid.',
        method: 'Accountmapping op de Cashweb-boekhouding. Definitie nog vast te stellen met finance (Frits).',
    },
    ltv_triple_lob: {
        description:
            'Verwachte totale klantwaarde over de hele relatie, met nadruk op klanten die in ≥3 business lines actief zijn.',
        method: 'Cashweb-omzet × marge × verwachte levensduur, gesegmenteerd op triple-LOB via HubSpot. Formule nog af te stemmen.',
    },
    ab_players: {
        description:
            'Aandeel medewerkers in de hoogste prestatiecategorieën (A/B-spelers).',
        method: 'Beoordelingsdata uit Hooray. Bron nog niet gekoppeld.',
    },
    marge_per_loon: {
        description:
            'Hoeveel brutomarge er tegenover elke euro loonkosten staat — efficiëntie-proxy zolang FTE-uren ontbreken.',
        method: 'Brutomarge (omzet − inkoop) gedeeld door loonkosten uit het Cashweb SAL-dagboek (debet).',
    },
    revenue_per_lob: {
        description: 'Omzet uitgesplitst per business line / sub-administratie.',
        method: 'Cashweb-omzet (debet, dagboeken 50 en VERK) gegroepeerd per sub_administration.',
    },

    // Operationeel — klantreis
    icp_interactions: {
        description:
            'Aantal betekenisvolle interacties met accounts die in het ideale klantprofiel (ICP) passen.',
        method: 'Proxy: nieuwe deals per week in HubSpot. ICP-tagging nog te definiëren.',
    },
    client_requests_lob: {
        description: 'Aanvragen van klanten, uitgesplitst per business line.',
        method: 'HubSpot. Nog niet gemeten.',
    },
    winrate: {
        description: 'Aandeel gewonnen deals ten opzichte van alle deals in de periode.',
        method: 'Gewonnen deals (gesloten én amount > 0) gedeeld door het totaal aantal deals (HubSpot).',
    },
    time_to_onboarding: {
        description: 'Doorlooptijd van een gewonnen deal tot een actieve, onboarded klant.',
        method: 'HubSpot: deal-close → onboarding. Gemiddelde doorlooptijd nog niet berekend.',
    },
    storage_lead_time: {
        description: 'Gemiddelde tijd tussen de geplande en de werkelijke leverdatum.',
        method: '7T Orderregel_Leverdata (werkelijk − gepland). Brontabel is leeg in deze 7T-export.',
    },
    occupancy_rate: {
        description: 'Aandeel magazijnlocaties dat bezet is.',
        method: '7T: bezette locaties gedeeld door alle pickbare, niet-geblokkeerde locaties.',
    },
    on_time_delivery: {
        description: 'Aandeel zendingen dat binnen de afgesproken termijn is geleverd.',
        method: 'Sprinter3000. Definitie van “op tijd” nog vast te leggen.',
    },
    churn: {
        description: 'Verloop van klanten of omzet over de periode.',
        method: 'Proxy: verloren deals en €0-deals in HubSpot.',
    },
    tickets: {
        description: 'Aantal support-tickets in de geselecteerde periode.',
        method: 'HubSpot Service Hub: telling met split open/gesloten.',
    },
    margin_per_shipment: {
        description: 'Gemiddelde brutomarge (GPM) per zending.',
        method: 'Sprinter3000: som van GPM gedeeld door het aantal zendingen.',
    },

    // Tactisch
    automation_goals: {
        description: 'Aandeel behaalde automatiseringsdoelen.',
        method: 'Nog geen gekoppelde bron.',
    },
    triple_lob_pct: {
        description: 'Aandeel klanten dat in ≥3 business lines omzet draait.',
        method: 'Cashweb: klanten met omzet in ≥3 LOB gedeeld door het totaal aantal klanten.',
    },
    enps: {
        description: 'Employee Net Promoter Score — medewerkerstevredenheid.',
        method: 'Microsoft Forms. Nog niet gemeten.',
    },
    nps: {
        description: 'Net Promoter Score, intern versus extern.',
        method: 'HubSpot. Nog niet gemeten.',
    },

    // Entiteit — AWC (7T)
    dock_to_stock: {
        description: 'Tijd van goederenontvangst tot beschikbaar in de voorraad.',
        method: '7T: ontvangst → putaway-timestamp. Brondata ontbreekt in deze 7T-export.',
    },
    perfect_order_rate: {
        description: 'Aandeel orders dat compleet, op tijd én onbeschadigd is geleverd.',
        method: 'Samengestelde KPI; vereist leverdatums (leeg) en schade-registratie (ontbreekt) in 7T.',
    },
    inventory_accuracy: {
        description: 'Aandeel tellingen waarbij het getelde aantal gelijk is aan het verwachte aantal.',
        method: '7T Telling_Locaties: voltooide tellingen met geteld == verwacht gedeeld door alle voltooide tellingen.',
    },
    otif: {
        description: 'On Time In Full — op tijd én volledig geleverd.',
        method: 'Vereist beloofde vs. werkelijke leverdatum plus volledige aantallen (7T Orderregel_Leverdata, leeg).',
    },
    throughput: {
        description: 'Doorzet van het magazijn — verwerkte volumes per periode.',
        method: 'Proxy: aantal ontvangsten binnen het lookback-venster (7T Ontvangsten).',
    },
    damage_rate: {
        description: 'Aandeel beschadigde goederen.',
        method: 'Vereist een schade-/afkeurveld in 7T — nog niet gevonden.',
    },

    // Entiteit — AFC (Sprinter3000)
    modal_split: {
        description: 'Verdeling van zendingen over de transportmodaliteiten.',
        method: 'Sprinter3000: aantal zendingen per shipment_mode.',
    },
    quote_conversion: {
        description: 'Aandeel offertes dat tot een boeking leidt.',
        method: 'Sprinter3000. Nog niet gemeten.',
    },
    margin_per_modality: {
        description: 'Gemiddelde GPM per transportmodaliteit.',
        method: 'Sprinter3000: gemiddelde GPM per shipment_mode.',
    },
    shipments_afc: {
        description: 'Aantal zendingen in de geselecteerde periode.',
        method: 'Sprinter3000: telling van shipments binnen het datumfilter.',
    },

    // Entiteit — ACC (Softpak)
    import_export_tickets: {
        description: 'Aantal import-, export- en consult-tickets.',
        method: 'Softpak. Nog niet gekoppeld.',
    },
    dossier_lead_time: {
        description: 'Doorlooptijd van dossier tot aangifte.',
        method: 'Softpak. Nog niet gemeten.',
    },
    first_time_right: {
        description: 'Aandeel aangiftes dat in één keer correct is.',
        method: 'Softpak. Nog niet gemeten.',
    },
};

export function kpiExplain(id) {
    return KPI_EXPLAIN[id] ?? null;
}

export function strategicLinkLabel(strategicId) {
    return STRATEGIC_KPIS[strategicId]?.label ?? strategicId;
}
