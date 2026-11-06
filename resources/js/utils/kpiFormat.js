const nlNumber = new Intl.NumberFormat('nl-NL');

/**
 * @param {number|null|undefined} n
 */
export function fmtRatio(n) {
    if (n == null || Number.isNaN(Number(n))) {
        return '';
    }

    return new Intl.NumberFormat('nl-NL', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(Number(n));
}

/**
 * @param {number|null|undefined} n
 * @param {{ suffix?: string }} [opts]
 */
export function fmtProcent(n, opts = {}) {
    if (n == null || Number.isNaN(Number(n))) {
        return '';
    }
    const s =
        new Intl.NumberFormat('nl-NL', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1,
        }).format(Number(n)) + '%';

    return opts.suffix ? `${s}${opts.suffix}` : s;
}

/**
 * @param {number|null|undefined} n
 */
export function fmtEuroValue(n) {
    if (n == null || Number.isNaN(Number(n))) {
        return '';
    }
    const v = Number(n);
    const abs = Math.abs(v);
    const sign = v < 0 ? '−' : '';

    if (abs >= 1_000_000) {
        return `${sign}€ ${new Intl.NumberFormat('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(abs / 1_000_000)} mln`;
    }
    if (abs >= 10_000) {
        return `${sign}€ ${nlNumber.format(Math.round(abs / 1000))}k`;
    }

    return `${sign}€ ${nlNumber.format(Math.round(abs))}`;
}

/**
 * @param {number|null|undefined} n
 */
export function fmtAantal(n) {
    if (n == null || Number.isNaN(Number(n))) {
        return '';
    }

    return nlNumber.format(Math.round(Number(n)));
}

/**
 * @param {number|null|undefined} n
 */
export function fmtDagen(n) {
    if (n == null || Number.isNaN(Number(n))) {
        return '';
    }

    return (
        new Intl.NumberFormat('nl-NL', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1,
        }).format(Number(n)) + ' dagen'
    );
}

/**
 * @param {number|null|undefined} n
 */
export function fmtScore(n) {
    if (n == null || Number.isNaN(Number(n))) {
        return '';
    }

    return nlNumber.format(Math.round(Number(n)));
}

/**
 * @param {string} eenheid
 * @param {number|null|undefined} waarde
 */
export function formatKpiValue(eenheid, waarde) {
    switch (eenheid) {
        case 'ratio':
            return fmtRatio(waarde);
        case 'procent':
            return fmtProcent(waarde);
        case 'euro':
            return fmtEuroValue(waarde);
        case 'aantal':
            return fmtAantal(waarde);
        case 'dagen':
            return fmtDagen(waarde);
        case 'score':
            return fmtScore(waarde);
        default:
            return waarde != null ? String(waarde) : '';
    }
}

/**
 * Mockup-weergave: groot getal + kleine eenheid ernaast ("2,40 ratio", "8,2 %", "66,7 dagen").
 *
 * @param {string} eenheid
 * @param {number|null|undefined} waarde
 * @returns {{ number: string, unit: string | null }}
 */
export function splitKpiValue(eenheid, waarde) {
    if (waarde == null || Number.isNaN(Number(waarde))) {
        return { number: '', unit: null };
    }
    switch (eenheid) {
        case 'ratio':
            return { number: fmtRatio(waarde), unit: 'ratio' };
        case 'procent':
            return { number: fmtProcent(waarde).replace('%', ''), unit: '%' };
        case 'dagen':
            return { number: fmtDagen(waarde).replace(' dagen', ''), unit: 'dagen' };
        case 'euro':
            return { number: fmtEuroValue(waarde), unit: null };
        case 'aantal':
            return { number: fmtAantal(waarde), unit: null };
        case 'score':
            return { number: fmtScore(waarde), unit: null };
        default:
            return { number: String(waarde), unit: null };
    }
}

/**
 * @param {string} eenheid
 * @param {number|null|undefined} delta
 */
export function formatKpiDelta(eenheid, delta) {
    if (delta == null || Number.isNaN(Number(delta))) {
        return null;
    }
    const d = Number(delta);
    if (d === 0) {
        return { text: 'gelijk', direction: 'flat' };
    }
    const sign = d > 0 ? '+' : '−';
    const abs = Math.abs(d);

    switch (eenheid) {
        case 'ratio':
            return {
                text: `${sign}${fmtRatio(abs)} t.o.v. vorige maand`,
                direction: d > 0 ? 'up' : 'down',
            };
        case 'procent':
            return {
                text: `${sign}${fmtProcent(abs).replace('%', '')} pp t.o.v. vorige maand`,
                direction: d > 0 ? 'up' : 'down',
            };
        case 'euro':
            return {
                text: `${sign}${fmtEuroValue(abs).replace(/^−/, '')}`,
                direction: d > 0 ? 'up' : 'down',
                rawDelta: d,
            };
        case 'aantal':
            return {
                text: `${sign}${fmtAantal(abs)}`,
                direction: d > 0 ? 'up' : 'down',
                rawDelta: d,
            };
        case 'dagen':
            return {
                text: `${sign}${new Intl.NumberFormat('nl-NL', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(abs)} dagen`,
                direction: d > 0 ? 'up' : 'down',
            };
        case 'score':
            return {
                text: `${sign}${fmtScore(abs)}`,
                direction: d > 0 ? 'up' : 'down',
            };
        default:
            return {
                text: `${sign}${abs}`,
                direction: d > 0 ? 'up' : 'down',
            };
    }
}

/**
 * Allowed frontend pct calc for euro/aantal only (Overdracht).
 *
 * @param {number|null|undefined} delta
 * @param {number|null|undefined} waardeVorige
 */
export function pctChangeFromDelta(delta, waardeVorige) {
    if (
        delta == null ||
        waardeVorige == null ||
        Number(waardeVorige) === 0 ||
        Number.isNaN(Number(delta)) ||
        Number.isNaN(Number(waardeVorige))
    ) {
        return null;
    }

    return Math.round((Number(delta) / Math.abs(Number(waardeVorige))) * 100);
}

/**
 * @param {'hoger_beter'|'lager_beter'|'neutraal'|string} richting
 * @param {'up'|'down'|'flat'} direction
 */
export function deltaSentiment(richting, direction) {
    if (direction === 'flat' || richting === 'neutraal') {
        return 'neutral';
    }
    const goodUp = richting === 'hoger_beter';
    if (direction === 'up') {
        return goodUp ? 'good' : 'bad';
    }

    return goodUp ? 'bad' : 'good';
}

/**
 * @param {string|null|undefined} isoDate
 */
export function formatStandPer(isoDate) {
    if (!isoDate) {
        return '';
    }
    const d = new Date(isoDate);
    if (Number.isNaN(d.getTime())) {
        return String(isoDate);
    }
    if (d.getUTCDate() === 1) {
        return new Intl.DateTimeFormat('nl-NL', {
            month: 'long',
            year: 'numeric',
            timeZone: 'UTC',
        }).format(d);
    }

    return new Intl.DateTimeFormat('nl-NL', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        timeZone: 'UTC',
    }).format(d);
}

export const STATE_LABELS = {
    meetwaarde: null,
    te_weinig_data: 'Te weinig data',
    wacht_op_invoer: 'Wacht op invoer',
    tbd: 'Definitie volgt',
    in_ontwikkeling: 'In ontwikkeling',
    in_opbouw: 'In opbouw',
    in_validatie: 'In validatie',
    data_onvolledig: 'Data onvolledig',
    niet_meetbaar: 'Niet meetbaar',
    data_ontbreekt: 'Data ontbreekt',
};
