<script setup>
import { computed, ref } from 'vue';
import AfcBlok from './AfcBlok.vue';
import Chart from 'primevue/chart';
import AfcInfo from '@/Components/Kpi/KpiInfo.vue';
import AfcKeuze from './AfcKeuze.vue';
import AfcSegment from './AfcSegment.vue';
import AfcTabel from './AfcTabel.vue';
import { MAANDEN_KORT, maandMetVorigJaar, perModaliteit } from '@/utils/afcAnalyse';
import { KLEUR, MODALITEIT_KLEUR, euroAs, tickStijl } from '@/utils/afcChart';
import { euro, getal, groeiKlasse, groeiTekst, procent } from '@/utils/afcFormat';

const props = defineProps({
    rows: { type: Array, required: true },
    jaar: { type: Number, required: true },
});

const tabel = computed(() => perModaliteit(props.rows, props.jaar));

const kolommen = [
    { key: 'modaliteit', label: 'Modaliteit' },
    { key: 'zendingen', label: 'Zendingen', fmt: getal, rechts: true },
    { key: 'omzet', label: 'Omzet', fmt: euro, rechts: true },
    { key: 'marge', label: 'Marge', fmt: euro, rechts: true },
    { key: 'margePct', label: 'Marge %', fmt: procent, rechts: true },
    { key: 'omzetVorig', label: 'Omzet vorig jaar', fmt: euro, rechts: true },
    { key: 'margeVorig', label: 'Marge vorig jaar', fmt: euro, rechts: true },
    { key: 'margePctVorig', label: 'Marge % vorig jaar', fmt: procent, rechts: true },
    { key: 'groeiOmzet', label: 'Groei omzet', fmt: groeiTekst, rechts: true, klasse: (r) => groeiKlasse(r.groeiOmzet) },
    { key: 'groeiMarge', label: 'Groei marge', fmt: groeiTekst, rechts: true, klasse: (r) => groeiKlasse(r.groeiMarge) },
];

const maat = ref('marge');
const maatOpties = [
    { value: 'marge', label: 'Marge' },
    { value: 'omzet', label: 'Omzet' },
    { value: 'zendingen', label: 'Zendingen' },
    { value: 'margePerZending', label: 'Marge per zending' },
    { value: 'margePct', label: 'Marge %' },
];
const modaliteit = ref('alle');
const modOpties = [
    { value: 'alle', label: 'Alle' },
    { value: 'Weg', label: 'Weg' },
    { value: 'Zee', label: 'Zee' },
    { value: 'Lucht', label: 'Lucht' },
];

const fmt = (v) => {
    if (v == null) {
        return '';
    }
    if (maat.value === 'zendingen') {
        return getal(v);
    }
    if (maat.value === 'margePct') {
        return procent(v);
    }

    return euro(v);
};

const maanden = computed(() =>
    maandMetVorigJaar(props.rows, props.jaar, { modaliteit: modaliteit.value, maat: maat.value }),
);
const kleur = computed(() => MODALITEIT_KLEUR[modaliteit.value] ?? KLEUR.blauw);
const isRatio = computed(() => maat.value === 'margePerZending' || maat.value === 'margePct');

const chartData = computed(() => ({
    labels: MAANDEN_KORT,
    datasets: [
        {
            type: 'bar',
            label: String(props.jaar),
            data: maanden.value.map((m) => m.nu),
            backgroundColor: maanden.value.map((m) => (m.open ? 'rgba(255,255,255,0)' : kleur.value)),
            borderColor: maanden.value.map((m) => (m.open ? kleur.value : 'transparent')),
            borderWidth: maanden.value.map((m) => (m.open ? 1.5 : 0)),
            borderRadius: 2,
            borderSkipped: false,
            maxBarThickness: 34,
            order: 2,
        },
        {
            type: 'line',
            label: String(props.jaar - 1),
            data: maanden.value.map((m) => m.vorig),
            showLine: false,
            pointStyle: 'line',
            pointRadius: 13,
            pointHoverRadius: 13,
            pointBorderWidth: 2.5,
            pointBorderColor: KLEUR.grijsDonker,
            borderColor: KLEUR.grijsDonker,
            order: 1,
        },
    ],
}));

const chartOptions = computed(() => ({
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
        legend: { display: false },
        tooltip: {
            filter: (item) => item.raw != null,
            callbacks: {
                title: (items) => {
                    const m = maanden.value[items[0].dataIndex];

                    return `${MAANDEN_KORT[m.maand - 1]}${m.open ? ' (nog niet compleet)' : ''}`;
                },
                label: (ctx) => `${ctx.dataset.label}: ${fmt(ctx.raw)}`,
            },
        },
    },
    scales: {
        x: { grid: { display: false }, ticks: { ...tickStijl, maxRotation: 0 } },
        y: {
            beginAtZero: !isRatio.value,
            grace: '5%',
            grid: { color: KLEUR.raster },
            border: { display: false },
            ticks: {
                ...tickStijl,
                maxTicksLimit: 6,
                callback: (v) =>
                    maat.value === 'zendingen' ? getal(v) : maat.value === 'margePct' ? procent(v) : euroAs(v),
            },
        },
    },
}));

/** Eén zin: hoeveel maanden boven vorig jaar, en de grootste uitschieter. */
const lezing = computed(() => {
    const vergelijkbaar = maanden.value.filter((m) => !m.open && m.nu != null && m.vorig != null);
    if (!vergelijkbaar.length) {
        return null;
    }
    const boven = vergelijkbaar.filter((m) => m.nu > m.vorig).length;
    const relatief = (m) => (m.vorig ? (m.nu - m.vorig) / Math.abs(m.vorig) : 0);
    const grootste = [...vergelijkbaar].sort((a, b) => Math.abs(relatief(b)) - Math.abs(relatief(a)))[0];
    const r = relatief(grootste) * 100;

    return `${boven} van de ${vergelijkbaar.length} afgesloten maanden boven ${props.jaar - 1}. Grootste verschil: ${MAANDEN_KORT[grootste.maand - 1]} (${groeiTekst(r)}).`;
});
</script>

<template>
    <AfcBlok
        :titel="`Per modaliteit, ${jaar} t/m vandaag naast dezelfde periode vorig jaar`"
        uitleg="Omzet excl. invoerrechten en btw. Invoerrechten (vooral zee-import) worden zonder marge doorbelast en tellen daarom niet mee."
    >
        <AfcTabel :kolommen="kolommen" :rijen="tabel" :rij-klasse="(r) => (r.isTotaal ? 'afc-totaal' : '')" />

        <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <h3 class="flex items-center gap-1.5 text-sm font-semibold text-gray-900">
                Per maand in {{ jaar }}, met {{ jaar - 1 }} ernaast
                <AfcInfo tekst="Op rapportagedatum in Sprinter. Het streepje is dezelfde maand een jaar eerder. Bij de jaarovergang krijgen openstaande dossiers 1 januari als datum; daarom springt januari omhoog (vooral zee). De lopende maand is alleen omlijnd: die is nog niet compleet." />
            </h3>
            <div class="flex flex-wrap items-center gap-3">
                <AfcSegment v-model="modaliteit" label="Modaliteit" :opties="modOpties" />
                <AfcKeuze v-model="maat" label="Toon" :opties="maatOpties" />
            </div>
        </div>
        <p v-if="lezing" class="mt-1 text-sm text-gray-700">{{ lezing }}</p>
        <div class="mt-3 h-64">
            <Chart type="bar" :data="chartData" :options="chartOptions" class="h-full w-full" />
        </div>
        <ul class="mt-2 flex gap-4 text-xs text-gray-600">
            <li class="flex items-center gap-1.5">
                <span class="inline-block h-2.5 w-2.5 rounded-sm" :style="{ background: kleur }" />{{ jaar }}
            </li>
            <li class="flex items-center gap-1.5">
                <span class="inline-block w-3 border-t-2 border-gray-600" />{{ jaar - 1 }}
            </li>
        </ul>
    </AfcBlok>
</template>
