import { fmtEuroValue } from '@/utils/kpiFormat';

const euro0 = new Intl.NumberFormat('nl-NL', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
});
const aantal = new Intl.NumberFormat('nl-NL', { maximumFractionDigits: 0 });
const een = new Intl.NumberFormat('nl-NL', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

const leeg = (n) => n == null || Number.isNaN(Number(n));

/** Volledig bedrag voor tabellen: € 1.234.567 */
export const euro = (n) => (leeg(n) ? '' : euro0.format(Math.round(Number(n))).replace('-', '−'));

/** Kort bedrag voor kaarten: € 6,72 mln / € 123k */
export const euroKort = (n) => (leeg(n) ? '' : fmtEuroValue(Number(n)));

export const getal = (n) => (leeg(n) ? '' : aantal.format(Math.round(Number(n))));

export const procent = (n) => (leeg(n) ? '' : `${een.format(Number(n))}%`);

/** Groei met teken: +4,2% / −3,1% */
export const groeiTekst = (n) => {
    if (leeg(n)) {
        return '';
    }
    const v = Number(n);

    return `${v > 0 ? '+' : v < 0 ? '−' : ''}${een.format(Math.abs(v))}%`;
};

export const groeiKlasse = (n) =>
    leeg(n) || Number(n) === 0 ? 'text-gray-500' : Number(n) > 0 ? 'text-emerald-700' : 'text-red-700';

export const datumKort = (iso) => {
    if (!iso) {
        return '';
    }
    const [j, m, d] = String(iso).slice(0, 10).split('-');

    return `${d}-${m}-${j}`;
};
