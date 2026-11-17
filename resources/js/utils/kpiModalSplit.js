/**
 * Modal split op de AFC-tegel: de verdeling weg / zee / lucht van één maand, plus het
 * aandeel zee en lucht per maand over twaalf maanden. Het KPI-getal (aandeel weg) zit
 * rond de 90%; wat beweegt is het deel dat niet over de weg gaat, dus dat krijgt de staven.
 *
 * Bron: kpi_afc_sprinter_maand (zendingen, weg, zee, lucht, status per maand).
 * Puur rekenwerk, geen Vue: de component KpiModalSplit tekent het resultaat.
 */
import { maandIndex, maandLabel } from '@/utils/kpiTegelGrafiek';

export const MODALITEITEN = [
    { key: 'weg', label: 'Weg', kleur: '#0496FF' },
    { key: 'zee', label: 'Zee', kleur: '#000000' },
    { key: 'lucht', label: 'Lucht', kleur: '#FF6700' },
];

const nl1 = new Intl.NumberFormat('nl-NL', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const nl0 = new Intl.NumberFormat('nl-NL', { maximumFractionDigits: 0 });

export const pct = (v) => `${nl1.format(v)}%`;
export const aantal = (v) => nl0.format(v);

function getal(v) {
    const n = Number(v);

    return Number.isFinite(n) ? n : 0;
}

/**
 * @param {Record<string, unknown>} r
 */
function maandRij(r) {
    const weg = getal(r.weg);
    const zee = getal(r.zee);
    const lucht = getal(r.lucht);
    const overig = getal(r.overig);
    const totaal = getal(r.zendingen) || weg + zee + lucht + overig;
    const aandeel = (n) => (totaal ? (100 * n) / totaal : 0);

    return {
        idx: maandIndex(r.maand),
        open: String(r.status ?? '') !== 'volledig',
        totaal,
        aantallen: { weg, zee, lucht },
        aandelen: { weg: aandeel(weg), zee: aandeel(zee), lucht: aandeel(lucht) },
        nietWeg: aandeel(zee + lucht),
    };
}

/**
 * @param {{ rows: Array<Record<string, unknown>>, standPer?: string|null }} p
 *   standPer: maand van het tegelgetal ('YYYY-MM-DD'); die maand toont de verdeling.
 */
export function bouwModalSplit({ rows, standPer = null }) {
    const perMaand = new Map();
    for (const r of rows ?? []) {
        const m = maandRij(r);
        if (!Number.isNaN(m.idx) && m.totaal > 0) {
            perMaand.set(m.idx, m);
        }
    }
    if (!perMaand.size) {
        return null;
    }
    const idxs = [...perMaand.keys()].sort((a, b) => a - b);

    // De maand van het tegelgetal; anders de laatste afgesloten maand; anders de laatste.
    const gevraagd = standPer ? maandIndex(standPer) : NaN;
    const kopIdx = perMaand.has(gevraagd)
        ? gevraagd
        : ([...idxs].reverse().find((i) => !perMaand.get(i).open) ?? idxs[idxs.length - 1]);
    const kop = perMaand.get(kopIdx);

    // Twaalf maanden t/m de laatste maand met data (de lopende maand staat er omlijnd bij).
    const eind = idxs[idxs.length - 1];
    const slots = [];
    for (let i = eind - 11; i <= eind; i++) {
        slots.push(i);
    }
    const inSlot = (i, f) => (perMaand.has(i) ? f(perMaand.get(i)) : null);

    // Lezing: aandeel zee en lucht in de kopmaand tegen een jaar eerder en het gemiddelde.
    const lezing = [];
    let gemiddelde = null;
    const vorig = perMaand.get(kopIdx - 12);
    if (vorig) {
        const d = kop.nietWeg - vorig.nietWeg;
        const teken = d > 0.05 ? '+' : d < -0.05 ? '−' : '±';
        lezing.push(`${teken}${nl1.format(Math.abs(d))} pp t.o.v. ${maandLabel(kopIdx - 12, true)}`);
    }
    const eerder = idxs.filter((i) => i < kopIdx && i >= kopIdx - 12 && !perMaand.get(i).open);
    if (eerder.length >= 6) {
        gemiddelde = eerder.reduce((s, i) => s + perMaand.get(i).nietWeg, 0) / eerder.length;
        lezing.push(`gem. ${pct(gemiddelde)} ervoor`);
    }

    return {
        kop: {
            label: maandLabel(kopIdx),
            kort: maandLabel(kopIdx, true),
            nietWeg: kop.nietWeg,
            open: kop.open,
            totaal: kop.totaal,
            delen: MODALITEITEN.map((m) => ({
                ...m,
                aantal: kop.aantallen[m.key],
                aandeel: kop.aandelen[m.key],
            })),
        },
        slots,
        labels: slots.map((i) => maandLabel(i)),
        kopIndex: slots.indexOf(kopIdx),
        open: slots.map((i) => inSlot(i, (m) => m.open) ?? false),
        zee: slots.map((i) => inSlot(i, (m) => m.aandelen.zee)),
        lucht: slots.map((i) => inSlot(i, (m) => m.aandelen.lucht)),
        weg: slots.map((i) => inSlot(i, (m) => m.aandelen.weg)),
        aantallen: slots.map((i) => inSlot(i, (m) => m.aantallen)),
        gemiddelde,
        lezing,
        startLabel: maandLabel(slots[0], true),
        eindLabel: maandLabel(slots[slots.length - 1], true),
    };
}
