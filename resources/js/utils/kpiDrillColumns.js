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
};

/**
 * @param {string} field
 */
export function drillColumnHeader(field) {
    return LABELS[field] ?? field.replace(/_/g, ' ');
}
