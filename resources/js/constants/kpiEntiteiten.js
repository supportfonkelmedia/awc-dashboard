/**
 * Entiteitfilter op het strategische scherm (feedback MT 10-11-2026).
 * `param` staat in de URL (?entiteit=awc), `scope` is de scope_code in Peliqan.
 */
export const KPI_ENTITEITEN = [
    { param: 'concern', scope: 'concern', label: 'Concern' },
    { param: 'awc', scope: 'alaw', label: 'AWC' },
    { param: 'afc', scope: 'pgl1', label: 'AFC' },
    { param: 'acc', scope: 'acco', label: 'ACC' },
];

export const ENTITEIT_SCOPES = new Set(
    KPI_ENTITEITEN.filter((e) => e.scope !== 'concern').map((e) => e.scope),
);

/**
 * @param {string|null|undefined} param
 * @returns {string} scope_code, valt terug op 'concern'
 */
export function scopeFromParam(param) {
    const hit = KPI_ENTITEITEN.find((e) => e.param === String(param ?? '').toLowerCase());

    return hit ? hit.scope : 'concern';
}

/**
 * @param {string} scope
 */
export function paramFromScope(scope) {
    return KPI_ENTITEITEN.find((e) => e.scope === scope)?.param ?? 'concern';
}

/**
 * Leesbare naam van een scope_code ('alaw' → 'AWC', 'Verkooppijplijn' blijft staan).
 *
 * @param {string|null|undefined} scope
 */
export function scopeLabel(scope) {
    const s = scope == null ? '' : String(scope);

    return KPI_ENTITEITEN.find((e) => e.scope === s)?.label ?? s;
}
