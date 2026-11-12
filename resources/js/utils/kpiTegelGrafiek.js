/**
 * Grafiek op een KPI-tegel: kiest per KPI een vorm (lijn of staven), legt het
 * venster vast (twaalf maanden), zet dezelfde maand een jaar eerder ernaast en
 * schrijft één korte lezing ("Hoogste sinds dec '24 · +12% t.o.v. vorig jaar").
 *
 * Puur rekenwerk, geen Vue: de component KpiTegelGrafiek tekent het resultaat.
 */

const MAANDEN = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];

const OPEN_STATUS = new Set(['voorlopig', 'onvolledig']);

/** Tellingen per maand: staven lezen beter dan een lijn. Rest volgt de heuristiek. */
const VORM_PER_KPI = {
    afc_zendingen: 'staven',
    throughput: 'staven',
    acc_dossiers: 'staven',
    churn: 'staven',
};

/** Eenheden waarvan het verschil in punten leest, niet in procenten. */
const VERSCHIL_IN_PUNTEN = new Set(['procent', 'ratio', 'dagen', 'score']);

/**
 * @param {string} periode 'YYYY-MM-DD' of 'YYYY-MM'
 * @returns {number} maandindex: jaar * 12 + (maand - 1)
 */
export function maandIndex(periode) {
    const s = String(periode ?? '');
    const jaar = Number(s.slice(0, 4));
    const maand = Number(s.slice(5, 7));
    if (!jaar || !maand) {
        return NaN;
    }

    return jaar * 12 + (maand - 1);
}

/** @param {number} idx */
export function maandLabel(idx, kort = false) {
    const jaar = Math.floor(idx / 12);
    const m = MAANDEN[idx - jaar * 12];

    return kort ? `${m} '${String(jaar).slice(2)}` : `${m} ${jaar}`;
}

/**
 * Eén punt per maand; bij dubbele maanden (definitief en voorlopig) wint de laatste.
 *
 * @param {Array<Record<string, unknown>>} points
 * @returns {Map<number, { waarde: number|null, open: boolean }>}
 */
function perMaand(points) {
    const map = new Map();
    const sorted = [...(points ?? [])].sort((a, b) =>
        String(a.periode ?? '').localeCompare(String(b.periode ?? '')),
    );
    for (const p of sorted) {
        const idx = maandIndex(p.periode);
        if (Number.isNaN(idx)) {
            continue;
        }
        const w = p.waarde == null || p.waarde === '' ? null : Number(p.waarde);
        map.set(idx, {
            waarde: Number.isFinite(w) ? w : null,
            open: OPEN_STATUS.has(String(p.status ?? 'definitief')),
        });
    }

    return map;
}

/**
 * Stap tussen de punten: 3 voor kwartaalreeksen, anders 1.
 *
 * @param {number[]} idxs gesorteerde maandindexen
 */
function stapGrootte(idxs) {
    if (idxs.length < 3) {
        return 1;
    }
    const gaten = [];
    for (let i = 1; i < idxs.length; i++) {
        gaten.push(idxs[i] - idxs[i - 1]);
    }
    gaten.sort((a, b) => a - b);

    return gaten[Math.floor(gaten.length / 2)] >= 3 ? 3 : 1;
}

/**
 * @param {{ kpiCode?: string|null, eenheid?: string|null, aantalSeries: number, stap: number }} p
 * @returns {'lijn'|'staven'}
 */
export function kiesVorm({ kpiCode, eenheid, aantalSeries, stap }) {
    if (kpiCode && VORM_PER_KPI[kpiCode]) {
        return VORM_PER_KPI[kpiCode];
    }
    if (aantalSeries > 1 || eenheid === 'aantal' || stap === 3) {
        return 'staven';
    }

    return 'lijn';
}

/**
 * Venster van twaalf maanden. Met een jaartal: dat kalenderjaar, ook de maanden die nog
 * komen (dan loopt alleen vorig jaar door). Zonder jaartal: de twaalf maanden t/m het laatste punt.
 *
 * @param {number[]} idxs
 * @param {string} periode 'all' of 'YYYY'
 * @param {number} stap
 * @returns {number[]}
 */
function venster(idxs, periode, stap) {
    if (!idxs.length) {
        return [];
    }
    const laatste = idxs[idxs.length - 1];
    let eind = laatste;
    if (/^\d{4}$/.test(String(periode))) {
        const jaar = Number(periode);
        // Kwartaalreeksen houden hun ritme (jan/apr/jul/okt of mrt/jun/sep/dec).
        const ritme = ((laatste % stap) + stap) % stap;
        eind = jaar * 12 + 11;
        while (((eind % stap) + stap) % stap !== ritme) {
            eind--;
        }
    }
    const slots = [];
    for (let i = eind - 12 + stap; i <= eind; i += stap) {
        slots.push(i);
    }

    return slots;
}

/**
 * @param {string|null|undefined} richting
 * @param {number} verschil
 * @returns {'good'|'bad'|'neutral'}
 */
function toon(richting, verschil) {
    if (!verschil || richting === 'neutraal' || !richting) {
        return 'neutral';
    }
    const goed = richting === 'lager_beter' ? verschil < 0 : verschil > 0;

    return goed ? 'good' : 'bad';
}

const nl1 = new Intl.NumberFormat('nl-NL', { maximumFractionDigits: 1 });
const nl2 = new Intl.NumberFormat('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/**
 * @param {string|null|undefined} eenheid
 * @param {number} nu
 * @param {number} toen
 * @returns {string|null}
 */
function verschilTekst(eenheid, nu, toen) {
    const d = nu - toen;
    const teken = d > 0 ? '+' : d < 0 ? '−' : '±';
    if (VERSCHIL_IN_PUNTEN.has(String(eenheid))) {
        if (eenheid === 'procent') {
            return `${teken}${nl1.format(Math.abs(d))} pp`;
        }
        if (eenheid === 'ratio') {
            return `${teken}${nl2.format(Math.abs(d))}`;
        }
        if (eenheid === 'dagen') {
            return `${teken}${nl1.format(Math.abs(d))} dagen`;
        }

        return `${teken}${nl1.format(Math.abs(d))}`;
    }
    if (!toen) {
        return null;
    }
    const pct = Math.round((d / Math.abs(toen)) * 100);

    return `${pct > 0 ? '+' : pct < 0 ? '−' : '±'}${Math.abs(pct)}%`;
}

/**
 * Korte lezing bij het laatste afgesloten punt: record en reeks eerst, dan vorig jaar.
 *
 * @param {{ totaal: Map<number, { waarde: number|null, open: boolean }>, eenheid?: string|null, richting?: string|null, stap: number, slots: number[], doel: number|null }} p
 * @returns {Array<{ tekst: string, toon: 'good'|'bad'|'neutral' }>}
 */
function lezing({ totaal, eenheid, richting, stap, slots, doel }) {
    const inVenster = new Set(slots);
    const compleet = [...totaal.entries()]
        .filter(([, p]) => !p.open && p.waarde != null)
        .sort((a, b) => a[0] - b[0]);
    const laatsteInVenster = compleet.filter(([i]) => inVenster.has(i)).pop();
    if (!laatsteInVenster) {
        return [];
    }
    const [idx, { waarde }] = laatsteInVenster;
    const tot = compleet.filter(([i]) => i <= idx);
    const delen = [];
    const eenheidWoord = stap === 3 ? 'kwartalen' : 'maanden';
    const maand = MAANDEN[idx % 12];
    const Maand = maand.charAt(0).toUpperCase() + maand.slice(1);

    // Record: hoogste of laagste van alle historie (minstens een jaar terug).
    const eerste = tot[0][0];
    if (tot.length >= 12 / stap + 1 && idx - eerste >= 12) {
        const eerder = tot.slice(0, -1).map(([, p]) => p.waarde);
        const sinds = maandLabel(eerste, true);
        if (waarde > Math.max(...eerder)) {
            delen.push({ tekst: `${Maand}: hoogste sinds ${sinds}`, toon: toon(richting, 1) });
        } else if (waarde < Math.min(...eerder)) {
            delen.push({ tekst: `${Maand}: laagste sinds ${sinds}`, toon: toon(richting, -1) });
        }
    }

    // Reeks: minstens drie keer op rij dezelfde kant op.
    if (!delen.length) {
        let n = 0;
        let richtingReeks = 0;
        for (let k = tot.length - 1; k > 0; k--) {
            const [i, p] = tot[k];
            const [j, q] = tot[k - 1];
            if (i - j !== stap) {
                break;
            }
            const r = Math.sign(p.waarde - q.waarde);
            if (r === 0 || (richtingReeks && r !== richtingReeks)) {
                break;
            }
            richtingReeks = r;
            n++;
        }
        if (n >= 3) {
            delen.push({
                tekst: `${n} ${eenheidWoord} op rij ${richtingReeks > 0 ? 'omhoog' : 'omlaag'}`,
                toon: toon(richting, richtingReeks),
            });
        }
    }

    // Zelfde maand een jaar eerder.
    const vorig = totaal.get(idx - 12);
    if (vorig && vorig.waarde != null) {
        const tekst = verschilTekst(eenheid, waarde, vorig.waarde);
        if (tekst) {
            delen.push({
                // Noemt het record de maand al, dan niet nog eens.
                tekst: `${delen.some((d) => d.tekst.startsWith(`${Maand}:`)) ? '' : `${Maand} `}${tekst} t.o.v. ${maandLabel(idx - 12, true)}`,
                toon: toon(richting, waarde - vorig.waarde),
            });
        }
    }

    // Geen record, reeks of vorig jaar: dan tegen het doel, anders tegen het gemiddelde.
    if (!delen.length && doel != null) {
        const boven = waarde >= doel;
        delen.push({
            tekst: `${Maand} ${boven ? 'boven' : 'onder'} doel (${verschilTekst(eenheid, waarde, doel)})`,
            toon: toon(richting, waarde - doel),
        });
    } else if (!delen.length && tot.length >= 4) {
        const eerder = tot.slice(-13, -1).map(([, p]) => p.waarde);
        const gem = eerder.reduce((a, b) => a + b, 0) / eerder.length;
        const tekst = verschilTekst(eenheid, waarde, gem);
        if (tekst) {
            delen.push({
                tekst: `${Maand} ${tekst} t.o.v. gemiddelde ervoor`,
                toon: toon(richting, waarde - gem),
            });
        }
    }

    return delen.slice(0, 2);
}

/**
 * @param {{
 *   series: Array<{ serie: string|null, points: Array<Record<string, unknown>> }>,
 *   periode?: string,
 *   kpiCode?: string|null,
 *   eenheid?: string|null,
 *   richting?: string|null,
 *   doel?: number|string|null,
 * }} p
 */
export function bouwTegelGrafiek({ series, periode = 'all', kpiCode = null, eenheid = null, richting = null, doel = null }) {
    const reeksen = (series ?? [])
        .map((s) => ({ serie: s.serie, maanden: perMaand(s.points) }))
        .filter((s) => s.maanden.size > 0);
    if (!reeksen.length) {
        return null;
    }

    // Totaal over de series (bij één serie is dat de serie zelf).
    const totaal = new Map();
    for (const r of reeksen) {
        for (const [idx, p] of r.maanden) {
            const cur = totaal.get(idx) ?? { waarde: null, open: false };
            totaal.set(idx, {
                waarde: p.waarde == null ? cur.waarde : (cur.waarde ?? 0) + p.waarde,
                open: cur.open || p.open,
            });
        }
    }

    const idxs = [...totaal.keys()].sort((a, b) => a - b);
    const stap = stapGrootte(idxs);
    const slots = venster(idxs, periode, stap);
    if (!slots.some((i) => totaal.has(i))) {
        return null;
    }
    const vorm = kiesVorm({ kpiCode, eenheid, aantalSeries: reeksen.length, stap });

    const vorig = slots.map((i) => totaal.get(i - 12)?.waarde ?? null);
    const heeftVorig = vorig.filter((v) => v != null).length >= Math.max(2, slots.length / 3);

    const doelGetal = doel == null || doel === '' ? null : Number(doel);
    const laatsteMetData = [...slots].reverse().find((i) => totaal.has(i));

    return {
        vorm,
        stap,
        slots,
        labels: slots.map((i) => maandLabel(i)),
        reeksen: reeksen.map((r) => ({
            serie: r.serie,
            data: slots.map((i) => r.maanden.get(i)?.waarde ?? null),
        })),
        totaal: slots.map((i) => totaal.get(i)?.waarde ?? null),
        open: slots.map((i) => totaal.get(i)?.open ?? false),
        laatste: slots.indexOf(laatsteMetData),
        vorig: heeftVorig ? vorig : null,
        vorigLabels: slots.map((i) => maandLabel(i - 12)),
        doel: Number.isFinite(doelGetal) ? doelGetal : null,
        lezing: lezing({
            totaal,
            eenheid,
            richting,
            stap,
            slots,
            doel: Number.isFinite(doelGetal) ? doelGetal : null,
        }),
        startLabel: maandLabel(slots[0], true),
        eindLabel: maandLabel(slots[slots.length - 1], true),
    };
}
