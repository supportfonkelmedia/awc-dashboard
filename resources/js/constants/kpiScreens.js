/** Matches `kpi_tegel_config.scherm` and `/kpi/{scherm}` routes (Overdracht). */
export const KPI_SCREENS = [
    'strategisch',
    'operationeel',
    'tactisch',
    'awc',
    'afc',
    'acc',
];

/** Top navigation (mockup). "Concern" is a group label for these three, not a tab. */
export const KPI_PRIMARY_TABS = [
    { id: 'strategisch', label: 'Strategisch', scherm: 'strategisch' },
    { id: 'operationeel', label: 'Operationeel', scherm: 'operationeel' },
    { id: 'tactisch', label: 'Tactisch', scherm: 'tactisch' },
];

export const KPI_TEAM_TABS = [
    { id: 'awc', label: 'AWC Warehouse', scherm: 'awc' },
    { id: 'afc', label: 'AFC Freight', scherm: 'afc' },
    { id: 'acc', label: 'ACC Customs', scherm: 'acc' },
];

export const KPI_SCREEN_META = {
    strategisch: {
        title: "MT-KPI's",
        subtitle: null,
    },
    operationeel: {
        title: 'De klantreis',
        subtitle:
            'Tegels zijn gegroepeerd op fase in de klantreis en voeden de MT-KPI’s.',
    },
    tactisch: {
        title: 'Tactisch en ondersteunend',
        subtitle: null,
    },
    awc: {
        title: 'Inslag, voorraad en uitslag',
        subtitle: 'Bronnen: 7T en Cashweb.',
    },
    afc: {
        title: 'Zendingen, marge en offertes',
        subtitle: 'Bronnen: Sprinter, Cashweb en HubSpot.',
    },
    acc: {
        title: 'Douanedossiers en doorlooptijd',
        subtitle: 'Bronnen: HubSpot en Cashweb.',
    },
};

export function kpiScreenRoute(scherm) {
    return route('kpi.screen', { scherm });
}

export function isKpiTabActive(tabScherm, currentScherm) {
    return tabScherm === currentScherm;
}
