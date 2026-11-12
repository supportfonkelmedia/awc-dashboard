<script setup>
import Chart from 'primevue/chart';
import { computed } from 'vue';
import { bouwTegelGrafiek } from '@/utils/kpiTegelGrafiek';
import { formatKpiValue } from '@/utils/kpiFormat';

const props = defineProps({
    /** Alle trendpunten per serie (niet gefilterd: vorig jaar komt hieruit). */
    series: { type: Array, default: () => [] },
    /** 'all' of een jaartal. */
    periode: { type: String, default: 'all' },
    kpiCode: { type: String, default: null },
    eenheid: { type: String, default: 'ratio' },
    richting: { type: String, default: null },
    doel: { type: [Number, String], default: null },
    heightClass: { type: String, default: 'h-20' },
    /** Assen tonen (detailpaneel); op de tegel blijft de grafiek kaal. */
    assen: { type: Boolean, default: false },
    emptyText: { type: String, default: 'Nog geen maandhistorie' },
});

// AWC-huisstijl.
const BLAUW = '#0496FF';
const BLAUW_ZACHT = 'rgba(4, 150, 255, 0.28)';
const GRIJS = '#A3A3A3';
const GROEN = '#059669';
const STAPEL = ['#0496FF', '#000000', '#8C8C8C', '#FF6700'];

const g = computed(() =>
    bouwTegelGrafiek({
        series: props.series,
        periode: props.periode,
        kpiCode: props.kpiCode,
        eenheid: props.eenheid,
        richting: props.richting,
        doel: props.doel,
    }),
);

const fmt = (v) => (v == null ? '' : formatKpiValue(props.eenheid, v) || String(v));

const chartData = computed(() => {
    const d = g.value;
    if (!d) {
        return { labels: [], datasets: [] };
    }
    const datasets = [];

    if (d.vorm === 'staven') {
        const gestapeld = d.reeksen.length > 1;
        d.reeksen.forEach((r, ri) => {
            const kleur = gestapeld ? STAPEL[ri % STAPEL.length] : BLAUW;
            datasets.push({
                type: 'bar',
                label: r.serie || 'Waarde',
                rol: 'huidig',
                data: r.data,
                // Laatste afgesloten periode vol, eerdere zacht, lopende periode alleen omlijnd.
                backgroundColor: r.data.map((_, i) =>
                    d.open[i]
                        ? 'rgba(255,255,255,0)'
                        : gestapeld || i === lastClosed.value
                          ? kleur
                          : BLAUW_ZACHT,
                ),
                borderColor: r.data.map((_, i) => (d.open[i] ? kleur : 'transparent')),
                borderWidth: r.data.map((_, i) => (d.open[i] ? 1.25 : 0)),
                borderRadius: 2,
                borderSkipped: false,
                maxBarThickness: 22,
                categoryPercentage: 0.78,
                barPercentage: 0.9,
                stack: 'nu',
                order: 2,
            });
        });
        if (d.vorig) {
            datasets.push({
                type: 'line',
                label: 'Jaar eerder',
                rol: 'vorig',
                data: d.vorig,
                showLine: false,
                pointStyle: 'line',
                pointRadius: 7,
                pointHoverRadius: 7,
                pointBorderWidth: 2,
                pointBorderColor: '#525252',
                borderColor: '#525252',
                order: 1,
            });
        }
    } else {
        if (d.vorig) {
            datasets.push({
                type: 'line',
                label: 'Jaar eerder',
                rol: 'vorig',
                data: d.vorig,
                borderColor: GRIJS,
                borderWidth: 1.25,
                borderDash: [3, 3],
                pointRadius: 0,
                pointHoverRadius: 2.5,
                tension: 0.3,
                spanGaps: true,
                order: 2,
            });
        }
        datasets.push({
            type: 'line',
            label: 'Waarde',
            rol: 'huidig',
            data: d.totaal,
            borderColor: BLAUW,
            borderWidth: 2,
            backgroundColor: 'rgba(4, 150, 255, 0.08)',
            fill: 'start',
            tension: 0.3,
            spanGaps: false,
            pointRadius: d.totaal.map((_, i) => (i === d.laatste || d.open[i] ? 2.75 : 0)),
            pointHoverRadius: 3,
            pointBackgroundColor: d.open.map((o) => (o ? '#fff' : BLAUW)),
            pointBorderColor: BLAUW,
            pointBorderWidth: 1.5,
            segment: {
                borderDash: (ctx) => (d.open[ctx.p1DataIndex] ? [4, 3] : undefined),
            },
            order: 1,
        });
    }

    if (d.doel != null) {
        datasets.push({
            type: 'line',
            label: 'Doel',
            rol: 'doel',
            data: d.slots.map(() => d.doel),
            borderColor: GROEN,
            borderWidth: 1,
            borderDash: [5, 4],
            pointRadius: 0,
            pointHoverRadius: 0,
            order: 0,
        });
    }

    return { labels: d.labels, datasets };
});

/** Index van de laatste afgesloten periode (die staaf krijgt de volle kleur). */
const lastClosed = computed(() => {
    const d = g.value;
    if (!d) {
        return -1;
    }
    for (let i = d.totaal.length - 1; i >= 0; i--) {
        if (d.totaal[i] != null && !d.open[i]) {
            return i;
        }
    }

    return -1;
});

const chartOptions = computed(() => {
    const d = g.value;
    const staven = d?.vorm === 'staven';

    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        layout: { padding: { left: 2, right: 4, top: 4, bottom: 0 } },
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: { display: false },
            tooltip: {
                filter: (item) => item.raw != null && item.dataset.rol !== 'doel',
                callbacks: {
                    title: (items) => {
                        const i = items[0]?.dataIndex;
                        if (i == null || !d) {
                            return '';
                        }

                        return d.open[i] ? `${d.labels[i]} (lopend)` : d.labels[i];
                    },
                    label: (ctx) => {
                        const i = ctx.dataIndex;
                        if (ctx.dataset.rol === 'vorig') {
                            return `${d.vorigLabels[i]}: ${fmt(ctx.raw)}`;
                        }
                        if (d.reeksen.length > 1) {
                            return `${ctx.dataset.label}: ${fmt(ctx.raw)}`;
                        }

                        return `${d.labels[i]}: ${fmt(ctx.raw)}`;
                    },
                    footer: (items) => {
                        if (!d || d.reeksen.length < 2) {
                            return '';
                        }
                        const i = items[0]?.dataIndex;

                        return i == null ? '' : `Totaal: ${fmt(d.totaal[i])}`;
                    },
                },
            },
        },
        scales: {
            x: {
                display: props.assen,
                stacked: staven,
                grid: { display: false },
                ticks: { color: '#737373', font: { size: 10 }, maxRotation: 0, autoSkip: true },
            },
            y: {
                display: props.assen,
                border: { display: false },
                grid: { color: '#EFEFEF' },
                ticks: { color: '#737373', font: { size: 10 }, maxTicksLimit: 5, callback: (v) => fmt(v) },
                stacked: staven && d?.reeksen.length > 1,
                beginAtZero: staven,
                grace: staven ? 0 : '8%',
            },
        },
    };
});

const toonKlasse = {
    good: 'text-emerald-700',
    bad: 'text-red-600',
    neutral: 'text-gray-600',
};
</script>

<template>
    <div v-if="g" class="w-full">
        <p v-if="g.lezing.length" class="mb-2 truncate text-[11px] leading-4">
            <template v-for="(deel, i) in g.lezing" :key="deel.tekst">
                <span v-if="i > 0" class="text-gray-300"> · </span>
                <span :class="toonKlasse[deel.toon]">{{ deel.tekst }}</span>
            </template>
        </p>
        <div :class="heightClass">
            <Chart
                :type="g.vorm === 'staven' ? 'bar' : 'line'"
                :data="chartData"
                :options="chartOptions"
                class="h-full w-full"
            />
        </div>
        <div class="mt-1 flex items-center justify-between gap-2 text-[9px] text-gray-500">
            <span :class="{ invisible: assen }">{{ g.startLabel }}</span>
            <span class="flex items-center gap-2.5">
                <span v-if="g.reeksen.length > 1" class="flex items-center gap-2">
                    <span v-for="(r, ri) in g.reeksen" :key="r.serie" class="flex items-center gap-1">
                        <span class="inline-block h-1.5 w-1.5 rounded-sm" :style="{ background: STAPEL[ri % STAPEL.length] }" />
                        {{ r.serie }}
                    </span>
                </span>
                <span v-if="g.vorig" class="flex items-center gap-1">
                    <span
                        class="inline-block w-3"
                        :class="g.vorm === 'staven' ? 'border-t-2 border-gray-600' : 'border-t border-dashed border-gray-400'"
                    />
                    jaar eerder
                </span>
                <span v-if="g.doel != null" class="flex items-center gap-1">
                    <span class="inline-block w-3 border-t border-dashed border-emerald-600" />
                    doel
                </span>
            </span>
            <span :class="{ invisible: assen }">{{ g.eindLabel }}</span>
        </div>
    </div>
    <div v-else :class="['relative flex w-full items-end', heightClass]">
        <div class="relative mb-2 w-full border-t border-dashed border-gray-300">
            <span
                class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white px-2 text-[10px] text-gray-500"
            >
                {{ emptyText }}
            </span>
        </div>
    </div>
</template>
