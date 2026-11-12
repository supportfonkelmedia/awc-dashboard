<script setup>
import Chart from 'primevue/chart';
import { computed } from 'vue';
import AfcInfo from '@/Components/Kpi/KpiInfo.vue';
import { margebrug } from '@/utils/afcAnalyse';
import { KLEUR, euroAs, tickStijl, waardeLabels } from '@/utils/afcChart';
import { euro, euroKort, getal, groeiTekst } from '@/utils/afcFormat';

const props = defineProps({
    /** kpi_afc_zending_maand, al gefilterd op richting. */
    rows: { type: Array, required: true },
    jaar: { type: Number, required: true },
    tmLabel: { type: String, required: true },
});

const brug = computed(() => margebrug(props.rows, props.jaar));

/** Volume plus één stap per modaliteit: met drie modaliteiten blijft het overzichtelijk. */
const stappen = computed(() => brug.value?.stappen ?? []);

const labels = computed(() => [
    `Marge ${props.jaar - 1}`,
    ...stappen.value.map((s) => s.label.replace('Marge per zending ', 'Per zending ')),
    `Marge ${props.jaar}`,
]);

/** Zwevende staven: [onder, boven] per stap. */
const balken = computed(() => {
    const b = brug.value;
    if (!b) {
        return [];
    }
    let stand = b.vorig;
    const tussen = stappen.value.map((s) => {
        const van = stand;
        stand += s.waarde;

        return [Math.min(van, stand), Math.max(van, stand)];
    });

    return [[asMin.value, b.vorig], ...tussen, [asMin.value, b.nu]];
});

/** De as begint net onder de laagste stand, anders verdwijnen de stappen naast de totalen. */
const asMin = computed(() => {
    const b = brug.value;
    if (!b) {
        return 0;
    }
    let stand = b.vorig;
    let laagste = Math.min(b.vorig, b.nu);
    let hoogste = Math.max(b.vorig, b.nu);
    for (const s of stappen.value) {
        stand += s.waarde;
        laagste = Math.min(laagste, stand);
        hoogste = Math.max(hoogste, stand);
    }
    const marge = Math.max((hoogste - laagste) * 1.2, Math.abs(hoogste) * 0.04);

    return Math.max(0, laagste - marge);
});

const waarde = (i) => {
    if (i === 0) {
        return brug.value.vorig;
    }
    if (i === labels.value.length - 1) {
        return brug.value.nu;
    }

    return stappen.value[i - 1].waarde;
};
const isTotaal = (i) => i === 0 || i === labels.value.length - 1;
const plus = (v) => (v > 0 ? '+' : v < 0 ? '−' : '±') + euroKort(Math.abs(v));

const chartData = computed(() => ({
    labels: labels.value,
    datasets: [
        {
            data: balken.value,
            backgroundColor: labels.value.map((_, i) =>
                isTotaal(i) ? (i === 0 ? KLEUR.grijs : KLEUR.zwart) : waarde(i) >= 0 ? KLEUR.groen : KLEUR.rood,
            ),
            borderRadius: 3,
            borderSkipped: false,
            maxBarThickness: 64,
            categoryPercentage: 0.8,
            barPercentage: 0.85,
            waardeLabel: (i) => (isTotaal(i) ? euroKort(waarde(i)) : plus(waarde(i))),
            labelKleur: (i) => (isTotaal(i) ? '#171717' : waarde(i) >= 0 ? KLEUR.groen : KLEUR.rood),
        },
    ],
}));

const chartOptions = computed(() => ({
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 22 } },
    plugins: {
        legend: { display: false },
        tooltip: {
            callbacks: {
                label: (ctx) => {
                    const i = ctx.dataIndex;
                    if (isTotaal(i)) {
                        return `Marge: ${euro(waarde(i))}`;
                    }
                    const s = stappen.value[i - 1];
                    const regels = [`Effect: ${(s.waarde > 0 ? '+' : '') + euro(s.waarde)}`];
                    if (s.soort === 'tarief') {
                        regels.push(`Marge per zending: ${euro(s.mpzVorig)} → ${euro(s.mpzNu)}`);
                    }
                    if (s.soort === 'volume') {
                        regels.push(`Zendingen: ${getal(brug.value.zendingenVorig)} → ${getal(brug.value.zendingenNu)}`);
                    }

                    return regels;
                },
            },
        },
    },
    scales: {
        x: { grid: { display: false }, ticks: { ...tickStijl, maxRotation: 0, autoSkip: false } },
        y: {
            min: asMin.value,
            grid: { color: KLEUR.raster },
            border: { display: false },
            ticks: { ...tickStijl, maxTicksLimit: 5, callback: euroAs },
        },
    },
}));

/** Eén zin: de grootste duw en de grootste rem. */
const lezing = computed(() => {
    const b = brug.value;
    if (!b) {
        return null;
    }
    const verschil = b.nu - b.vorig;
    const g = b.vorig ? (100 * verschil) / Math.abs(b.vorig) : null;
    const omschrijf = (s) =>
        s.soort === 'volume'
            ? `${b.zendingenNu >= b.zendingenVorig ? 'meer' : 'minder'} zendingen (${plus(s.waarde)})`
            : `${s.waarde >= 0 ? 'hogere' : 'lagere'} marge per zending ${s.label.replace('Marge per zending ', '').toLowerCase()} (${plus(s.waarde)})`;
    const gesorteerd = [...b.stappen].sort((x, y) => Math.abs(y.waarde) - Math.abs(x.waarde));
    const hoofd = gesorteerd[0];
    const tegen = gesorteerd.find((s) => Math.sign(s.waarde) !== Math.sign(verschil) && Math.abs(s.waarde) >= Math.abs(b.vorig) * 0.005);
    let zin = `Marge ${plus(verschil)}${g != null ? ` (${groeiTekst(g)})` : ''}, vooral door ${omschrijf(hoofd)}`;
    if (tegen) {
        zin += `; ${omschrijf(tegen)} ${verschil >= 0 ? 'drukte' : 'hielp'} het resultaat`;
    }

    return `${zin}.`;
});
</script>

<template>
    <div v-if="brug" class="rounded-xl border border-gray-200 bg-white p-5 lg:p-6">
        <h2 class="flex items-center gap-1.5 text-base font-semibold text-gray-900">
            Waar komt het margeverschil vandaan?
            <AfcInfo
                :tekst="[
                    `Brutomarge ${jaar} t/m ${tmLabel} tegen dezelfde periode in ${jaar - 1}, gesplitst per oorzaak.`,
                    'Aantal zendingen: meer of minder zendingen tegen de marge per zending van vorig jaar (per modaliteit, dus inclusief verschuiving tussen weg, zee en lucht).',
                    'Per zending: wat een hogere of lagere marge per zending opleverde bij het aantal zendingen van nu. De stappen tellen precies op tot het verschil.',
                    'De as begint niet bij nul, zodat de stappen leesbaar blijven naast de totalen.',
                ]"
            />
        </h2>
        <p v-if="lezing" class="mt-1 max-w-4xl text-sm text-gray-700">{{ lezing }}</p>
        <div class="mt-4 h-64">
            <Chart type="bar" :data="chartData" :options="chartOptions" :plugins="[waardeLabels]" class="h-full w-full" />
        </div>
    </div>
</template>
