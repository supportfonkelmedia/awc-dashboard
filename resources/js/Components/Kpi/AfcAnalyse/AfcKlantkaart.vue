<script setup>
import Chart from 'primevue/chart';
import { computed } from 'vue';
import { KLEUR, euroAs, tickStijl } from '@/utils/afcChart';
import { euro, euroKort, getal, procent } from '@/utils/afcFormat';

const props = defineProps({
    /** Rijen uit topKlanten(): naam, omzet, marge, margePct, zendingen. */
    klanten: { type: Array, required: true },
    /** Onder deze marge (in %) kleurt een klant oranje. */
    grens: { type: Number, default: 10 },
});

const punten = computed(() => props.klanten.filter((k) => k.omzet > 0 && k.margePct != null));

const gemiddeld = computed(() => {
    const omzet = punten.value.reduce((s, k) => s + k.omzet, 0);
    const marge = punten.value.reduce((s, k) => s + k.marge, 0);

    return omzet ? (100 * marge) / omzet : null;
});

const maxZendingen = computed(() => Math.max(1, ...punten.value.map((k) => k.zendingen)));
const straal = (z) => 4 + 14 * Math.sqrt(z / maxZendingen.value);

const chartData = computed(() => ({
    datasets: [
        {
            data: punten.value.map((k) => ({ x: k.omzet, y: k.margePct, r: straal(k.zendingen), k })),
            backgroundColor: punten.value.map((k) =>
                k.margePct < props.grens ? 'rgba(255, 103, 0, 0.55)' : 'rgba(4, 150, 255, 0.45)',
            ),
            borderColor: punten.value.map((k) => (k.margePct < props.grens ? KLEUR.oranje : KLEUR.blauw)),
            borderWidth: 1,
        },
        {
            type: 'line',
            label: 'gemiddeld',
            data: punten.value.length
                ? [
                      { x: Math.min(...punten.value.map((k) => k.omzet)), y: gemiddeld.value },
                      { x: Math.max(...punten.value.map((k) => k.omzet)), y: gemiddeld.value },
                  ]
                : [],
            borderColor: KLEUR.grijs,
            borderDash: [4, 4],
            borderWidth: 1,
            pointRadius: 0,
            pointHoverRadius: 0,
        },
    ],
}));

const chartOptions = computed(() => ({
    maintainAspectRatio: false,
    animation: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            filter: (item) => item.datasetIndex === 0,
            callbacks: {
                title: (items) => items[0]?.raw?.k?.naam ?? '',
                label: (ctx) => {
                    const k = ctx.raw.k;

                    return [
                        `Omzet: ${euro(k.omzet)}`,
                        `Marge: ${euro(k.marge)} (${procent(k.margePct)})`,
                        `Zendingen: ${getal(k.zendingen)}`,
                    ];
                },
            },
        },
    },
    scales: {
        x: {
            type: 'logarithmic',
            title: { display: true, text: 'Omzet (log-schaal)', ...tickStijl },
            grid: { color: KLEUR.raster },
            ticks: {
                ...tickStijl,
                callback: (v) => {
                    const macht = v / 10 ** Math.floor(Math.log10(v));

                    return [1, 2, 5].includes(Math.round(macht)) ? euroAs(v) : '';
                },
            },
        },
        y: {
            title: { display: true, text: 'Marge %', ...tickStijl },
            grid: { color: (ctx) => (ctx.tick.value === props.grens ? '#FDBA74' : KLEUR.raster) },
            border: { display: false },
            ticks: { ...tickStijl, callback: (v) => `${v}%` },
        },
    },
}));

/** Grote klanten met een dunne marge: daar zit de meeste winst om te halen. */
const lezing = computed(() => {
    const dun = punten.value.filter((k) => k.margePct < props.grens);
    if (!punten.value.length) {
        return null;
    }
    if (!dun.length) {
        return `Alle ${punten.value.length} klanten zitten op of boven ${props.grens}% marge; gemiddeld ${procent(gemiddeld.value)}.`;
    }
    const omzet = dun.reduce((s, k) => s + k.omzet, 0);
    const grootste = [...dun].sort((a, b) => b.omzet - a.omzet)[0];

    return `${dun.length} van de ${punten.value.length} grootste klanten zitten onder ${props.grens}% marge, samen ${euroKort(omzet)} omzet. De grootste: ${grootste.klant} (${euroKort(grootste.omzet)}, ${procent(grootste.margePct)}).`;
});
</script>

<template>
    <div v-if="punten.length">
        <p v-if="lezing" class="text-sm text-gray-700">{{ lezing }}</p>
        <div class="mt-3 h-72">
            <Chart type="bubble" :data="chartData" :options="chartOptions" class="h-full w-full" />
        </div>
        <ul class="mt-2 flex flex-wrap gap-4 text-xs text-gray-600">
            <li class="flex items-center gap-1.5">
                <span class="inline-block h-2.5 w-2.5 rounded-full bg-awc-orange/60 ring-1 ring-awc-orange" />
                onder {{ grens }}% marge
            </li>
            <li class="flex items-center gap-1.5">
                <span class="inline-block h-2.5 w-2.5 rounded-full ring-1" style="background: rgba(4, 150, 255, 0.45); --tw-ring-color: #0496ff" />
                {{ grens }}% of meer
            </li>
            <li class="flex items-center gap-1.5">
                <span class="inline-block w-3 border-t border-dashed border-gray-400" />
                gemiddeld {{ procent(gemiddeld) }}
            </li>
            <li>Grootte = aantal zendingen</li>
        </ul>
    </div>
</template>
