<script setup>
import { computed, ref, watch } from 'vue';
import AfcBlok from './AfcBlok.vue';
import Chart from 'primevue/chart';
import AfcKeuze from './AfcKeuze.vue';
import AfcTabel from './AfcTabel.vue';
import { MAANDEN_KORT, cumulatiefVerschil, resultaatPerJaar } from '@/utils/afcAnalyse';
import { KLEUR, euroAs, tickStijl } from '@/utils/afcChart';
import { euro, euroKort, groeiKlasse, groeiTekst, procent } from '@/utils/afcFormat';

const plusKort = (v) => (v == null ? '' : (v > 0 ? '+' : '') + euroKort(v));

const props = defineProps({
    rows: { type: Array, required: true },
    lopendJaar: { type: Number, required: true },
    laatsteVolleMaand: { type: Number, required: true },
    geldtNiet: { type: String, default: null },
});

const tmMaand = ref(props.laatsteVolleMaand || 12);
// Ander jaar gekozen: terug naar de laatste volle maand van dat jaar.
watch(
    () => [props.lopendJaar, props.laatsteVolleMaand],
    () => {
        tmMaand.value = props.laatsteVolleMaand || 12;
    },
);
const toon = ref('resultaat_voor_belasting');

const maandOpties = computed(() =>
    MAANDEN_KORT.map((m, i) => ({
        value: i + 1,
        label: i + 1 === props.laatsteVolleMaand ? `${m} (laatste volle maand)` : m,
    })),
);

const perJaar = computed(() => resultaatPerJaar(props.rows, tmMaand.value));

const kolommen = [
    { key: 'jaar', label: 'Jaar' },
    { key: 'omzet', label: 'Omzet (8xxx)', fmt: euroKort, rechts: true },
    { key: 'kostprijs', label: 'Kostprijs (6xxx)', fmt: euroKort, rechts: true },
    { key: 'brutomarge', label: 'Brutomarge', fmt: euroKort, rechts: true },
    { key: 'brutomargePct', label: 'Brutomarge %', fmt: procent, rechts: true },
    { key: 'bedrijfskosten', label: 'Bedrijfskosten (4xxx)', fmt: euroKort, rechts: true },
    { key: 'overig', label: 'Overig (9000)', fmt: euroKort, rechts: true },
    { key: 'resultaat', label: 'Resultaat vóór belasting', fmt: euroKort, rechts: true },
    { key: 'groeiOmzet', label: 'Groei omzet', fmt: groeiTekst, rechts: true, klasse: (r) => groeiKlasse(r.groeiOmzet) },
    { key: 'resultaatVerschil', label: 'Resultaat t.o.v. vorig jaar', fmt: plusKort, rechts: true, klasse: (r) => groeiKlasse(r.resultaatVerschil) },
];

const toonOpties = [
    { value: 'resultaat_voor_belasting', label: 'Resultaat vóór belasting' },
    { value: 'omzet', label: 'Omzet' },
    { value: 'brutomarge', label: 'Brutomarge' },
];

const verschil = computed(() => cumulatiefVerschil(props.rows, toon.value, props.lopendJaar, tmMaand.value));
const toonLabel = computed(() => toonOpties.find((o) => o.value === toon.value)?.label.toLowerCase() ?? '');

const chartData = computed(() => ({
    labels: MAANDEN_KORT,
    datasets: [
        {
            data: verschil.value.map((r) => r.verschil),
            backgroundColor: verschil.value.map((r) => ((r.verschil ?? 0) >= 0 ? KLEUR.groen : KLEUR.rood)),
            borderRadius: 2,
            maxBarThickness: 28,
        },
    ],
}));

const chartOptions = computed(() => ({
    maintainAspectRatio: false,
    animation: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            filter: (item) => item.raw != null,
            callbacks: {
                title: (items) => `t/m ${MAANDEN_KORT[items[0].dataIndex]}`,
                label: (ctx) => {
                    const r = verschil.value[ctx.dataIndex];

                    return [
                        `${props.lopendJaar}: ${euro(r.nu)}`,
                        `${props.lopendJaar - 1}: ${euro(r.vorig)}`,
                        `Verschil: ${(r.verschil > 0 ? '+' : '') + euro(r.verschil)}`,
                    ];
                },
            },
        },
    },
    scales: {
        x: { grid: { display: false }, ticks: { ...tickStijl, maxRotation: 0 } },
        y: {
            grid: { color: (ctx) => (ctx.tick.value === 0 ? '#A3A3A3' : KLEUR.raster) },
            border: { display: false },
            ticks: { ...tickStijl, maxTicksLimit: 6, callback: euroAs },
        },
    },
}));

/** Eén zin: voor of achter, en sinds wanneer dat zo is. */
const lezing = computed(() => {
    const punten = verschil.value.filter((r) => r.verschil != null);
    if (!punten.length) {
        return null;
    }
    const laatste = punten[punten.length - 1];
    const voor = laatste.verschil >= 0;
    let sinds = punten.length - 1;
    while (sinds > 0 && punten[sinds - 1].verschil >= 0 === voor) {
        sinds--;
    }
    const wanneer = sinds === 0 ? 'het hele jaar al' : `sinds ${MAANDEN_KORT[punten[sinds].maand - 1]}`;

    return `T/m ${MAANDEN_KORT[laatste.maand - 1]} ${euroKort(Math.abs(laatste.verschil))} ${voor ? 'voor' : 'achter'} op ${props.lopendJaar - 1} (${toonLabel.value}), ${wanneer}.`;
});
</script>

<template>
    <AfcBlok
        :geldt-niet="geldtNiet"
        :titel="`Resultaat volgens Cash t/m ${MAANDEN_KORT[tmMaand - 1]}, per jaar`"
        :uitleg="[
            'Grootboek in Cash, per grootboekperiode: dezelfde maand als de MT-tegels bruto marge en EBITDA. Vennootschapsbelasting (9100) en de afsluitboeking (9993) tellen niet mee.',
            'Niet afgesloten maanden missen vaak nog kosten; jaarafsluiting landt in december.',
            'Het richtingfilter geldt hier niet: Cash kent geen richting.',
        ]"
    >
        <template #acties>
            <AfcKeuze v-model="tmMaand" label="T/m maand" :opties="maandOpties" />
        </template>

        <AfcTabel :kolommen="kolommen" :rijen="perJaar" />

        <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <h3 class="text-sm font-semibold text-gray-900">
                Voor of achter op {{ lopendJaar - 1 }}, cumulatief per maand
            </h3>
            <AfcKeuze v-model="toon" label="Toon" :opties="toonOpties" />
        </div>
        <p v-if="lezing" class="mt-1 text-sm text-gray-700">{{ lezing }}</p>
        <div class="mt-3 h-64">
            <Chart type="bar" :data="chartData" :options="chartOptions" class="h-full w-full" />
        </div>
    </AfcBlok>
</template>
