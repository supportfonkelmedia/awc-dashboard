<script setup>
import Chart from 'primevue/chart';
import { computed } from 'vue';
import { euro, getal } from '@/utils/afcFormat';

const props = defineProps({
    type: { type: String, default: 'line' },
    labels: { type: Array, required: true },
    /** [{ label, data, kleur }] */
    reeksen: { type: Array, required: true },
    eenheid: { type: String, default: 'euro' },
    gestapeld: { type: Boolean, default: false },
    hoogte: { type: String, default: 'h-72' },
});

const fmt = (v) => (props.eenheid === 'euro' ? euro(v) : getal(v));

const data = computed(() => ({
    labels: props.labels,
    datasets: props.reeksen.map((r) => ({
        label: r.label,
        data: r.data,
        borderColor: r.kleur,
        backgroundColor: props.type === 'bar' ? r.kleur : 'transparent',
        borderWidth: props.type === 'bar' ? 0 : 2,
        pointRadius: 0,
        pointHoverRadius: 3,
        tension: 0.25,
        spanGaps: false,
        maxBarThickness: 18,
    })),
}));

const options = computed(() => ({
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
        legend: { display: false },
        tooltip: {
            callbacks: {
                label: (ctx) => `${ctx.dataset.label}: ${fmt(ctx.parsed.y)}`,
            },
        },
    },
    scales: {
        x: {
            stacked: props.gestapeld,
            grid: { display: false },
            ticks: { color: '#737373', font: { size: 11 }, maxRotation: 0, autoSkip: true },
        },
        y: {
            stacked: props.gestapeld,
            grid: { color: '#EBEBEB' },
            border: { display: false },
            ticks: {
                color: '#737373',
                font: { size: 11 },
                callback: (v) =>
                    props.eenheid === 'euro'
                        ? Math.abs(v) >= 1_000_000
                            ? `€ ${(v / 1_000_000).toLocaleString('nl-NL')} mln`
                            : `€ ${Math.round(v / 1000).toLocaleString('nl-NL')}k`
                        : getal(v),
            },
        },
    },
}));
</script>

<template>
    <div>
        <ul class="mb-3 flex flex-wrap gap-4 text-xs text-gray-600">
            <li v-for="r in reeksen" :key="r.label" class="flex items-center gap-1.5">
                <span class="inline-block h-2.5 w-2.5 rounded-sm" :style="{ background: r.kleur }" />
                {{ r.label }}
            </li>
        </ul>
        <div :class="hoogte">
            <Chart :type="type" :data="data" :options="options" class="h-full w-full" />
        </div>
    </div>
</template>
