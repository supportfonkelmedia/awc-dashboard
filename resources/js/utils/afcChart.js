/**
 * Gedeelde Chart.js-bouwstenen voor de AFC-analyse: kleuren, as-opmaak en een
 * kleine plugin die waarden boven staven zet (zonder extra dependency).
 */

export const KLEUR = {
    blauw: '#0496FF',
    blauwZacht: 'rgba(4, 150, 255, 0.28)',
    zwart: '#000000',
    grijs: '#A3A3A3',
    grijsDonker: '#525252',
    oranje: '#FF6700',
    groen: '#059669',
    rood: '#DC2626',
    raster: '#EFEFEF',
    tekst: '#737373',
};

export const MODALITEIT_KLEUR = { Weg: '#0496FF', Zee: '#000000', Lucht: '#FF6700' };

/** As-label in euro's: € 1,2 mln / € 340k / € 900. */
export function euroAs(v) {
    const a = Math.abs(v);
    const teken = v < 0 ? '−' : '';
    if (a >= 1_000_000) {
        return `${teken}€ ${(a / 1_000_000).toLocaleString('nl-NL', { maximumFractionDigits: 1 })} mln`;
    }
    if (a >= 1000) {
        return `${teken}€ ${Math.round(a / 1000).toLocaleString('nl-NL')}k`;
    }

    return `${teken}€ ${Math.round(a).toLocaleString('nl-NL')}`;
}

export const tickStijl = { color: KLEUR.tekst, font: { size: 11 } };

/**
 * Zet per staaf een label erboven (of eronder bij negatieve waarden).
 * Dataset-optie `waardeLabel: (index) => string|null` bepaalt de tekst.
 */
export const waardeLabels = {
    id: 'afcWaardeLabels',
    afterDatasetsDraw(chart) {
        const { ctx } = chart;
        chart.data.datasets.forEach((ds, di) => {
            if (typeof ds.waardeLabel !== 'function' || !chart.isDatasetVisible(di)) {
                return;
            }
            const meta = chart.getDatasetMeta(di);
            meta.data.forEach((el, i) => {
                const tekst = ds.waardeLabel(i);
                if (!tekst) {
                    return;
                }
                const { x, y, base } = el.getProps(['x', 'y', 'base'], true);
                const boven = Math.min(y, base);
                const onder = Math.max(y, base);
                const negatief = ds.labelOnder?.(i) ?? false;
                ctx.save();
                ctx.font = '600 11px Figtree, ui-sans-serif, system-ui, sans-serif';
                ctx.fillStyle = ds.labelKleur?.(i) ?? '#171717';
                ctx.textAlign = 'center';
                ctx.textBaseline = negatief ? 'top' : 'bottom';
                ctx.fillText(tekst, x, negatief ? onder + 4 : boven - 4);
                ctx.restore();
            });
        });
    },
};
