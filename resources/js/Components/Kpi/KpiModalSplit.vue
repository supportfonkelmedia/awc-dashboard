<script setup>
import Chart from 'primevue/chart';
import { computed } from 'vue';
import { aantal, bouwModalSplit, pct } from '@/utils/kpiModalSplit';

/**
 * Modal split op de tegel: één balk met de verdeling weg / zee / lucht in de maand van het
 * tegelgetal, daaronder het aandeel zee en lucht per maand (het deel dat beweegt).
 */
const props = defineProps({
    /** Rijen uit kpi_afc_sprinter_maand. */
    rows: { type: Array, default: () => [] },
    /** Maand van het tegelgetal ('YYYY-MM-DD'). */
    standPer: { type: String, default: null },
    heightClass: { type: String, default: 'h-14' },
});

const s = computed(() => bouwModalSplit({ rows: props.rows, standPer: props.standPer }));

const balkLabel = computed(() =>
    s.value
        ? `${s.value.kop.label}: ${s.value.kop.delen.map((d) => `${d.label} ${pct(d.aandeel)}`).join(', ')}`
        : '',
);

const zee = computed(() => s.value?.kop.delen.find((d) => d.key === 'zee'));
const lucht = computed(() => s.value?.kop.delen.find((d) => d.key === 'lucht'));

/** Eerdere maanden zacht, de maand van het tegelgetal vol, de lopende maand alleen omlijnd. */
function vulling(kleur, zacht) {
    return s.value.open.map((open, i) => {
        if (open) {
            return 'rgba(255,255,255,0)';
        }

        return i === s.value.kopIndex ? kleur : zacht;
    });
}

const chartData = computed(() => {
    const d = s.value;
    if (!d) {
        return { labels: [], datasets: [] };
    }
    const staaf = (label, data, kleur, zacht) => ({
        type: 'bar',
        label,
        data,
        backgroundColor: vulling(kleur, zacht),
        borderColor: d.open.map((o) => (o ? kleur : 'transparent')),
        borderWidth: d.open.map((o) => (o ? 1.25 : 0)),
        borderRadius: 2,
        borderSkipped: false,
        maxBarThickness: 22,
        categoryPercentage: 0.78,
        barPercentage: 0.9,
        stack: 'nietWeg',
    });

    const datasets = [
        staaf('Zee', d.zee, zee.value.kleur, 'rgba(0, 0, 0, 0.32)'),
        staaf('Lucht', d.lucht, lucht.value.kleur, 'rgba(255, 103, 0, 0.45)'),
    ];
    // Het gemiddelde uit de lezing als lijn: geeft de staven zonder as een maat.
    if (d.gemiddelde != null) {
        datasets.push({
            type: 'line',
            label: 'Gemiddeld',
            rol: 'gem',
            data: d.slots.map(() => d.gemiddelde),
            borderColor: '#737373',
            borderWidth: 1,
            borderDash: [3, 3],
            pointRadius: 0,
            pointHoverRadius: 0,
            order: -1,
        });
    }

    return { labels: d.labels, datasets };
});

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { left: 2, right: 4, top: 4, bottom: 0 } },
    interaction: { mode: 'index', intersect: false },
    plugins: {
        legend: { display: false },
        tooltip: {
            filter: (item) => item.raw != null && item.dataset.rol !== 'gem',
            callbacks: {
                title: (items) => {
                    const i = items[0]?.dataIndex;
                    if (i == null) {
                        return '';
                    }

                    return s.value.open[i] ? `${s.value.labels[i]} (voorlopig)` : s.value.labels[i];
                },
                label: (ctx) => {
                    const n = s.value.aantallen[ctx.dataIndex]?.[ctx.dataset.label.toLowerCase()];

                    return `${ctx.dataset.label}: ${pct(ctx.raw)} (${aantal(n ?? 0)})`;
                },
                footer: (items) => {
                    const i = items[0]?.dataIndex;
                    const w = i == null ? null : s.value.weg[i];
                    if (w == null) {
                        return '';
                    }

                    return `Weg: ${pct(w)} (${aantal(s.value.aantallen[i].weg)})`;
                },
            },
        },
    },
    scales: {
        x: { display: false, stacked: true },
        y: { display: false, stacked: true, beginAtZero: true, grace: '4%' },
    },
}));
</script>

<template>
    <div v-if="s" class="w-full">
        <!-- Verdeling in de maand van het tegelgetal. -->
        <div
            class="flex h-2.5 w-full gap-px overflow-hidden rounded-full bg-gray-100"
            role="img"
            :aria-label="balkLabel"
        >
            <span
                v-for="d in s.kop.delen"
                v-show="d.aantal > 0"
                :key="d.key"
                class="h-full min-w-[3px]"
                :style="{ width: `${d.aandeel}%`, background: d.kleur }"
            />
        </div>
        <ul class="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] leading-4 text-gray-600">
            <li v-for="d in s.kop.delen" :key="d.key" class="flex items-center gap-1">
                <span class="inline-block h-2 w-2 rounded-sm" :style="{ background: d.kleur }" aria-hidden="true" />
                <span class="font-medium text-gray-900">{{ d.label }}</span>
                <span class="tabular-nums">{{ pct(d.aandeel) }}</span>
                <span class="tabular-nums text-gray-400">({{ aantal(d.aantal) }})</span>
            </li>
        </ul>

        <!-- Het deel dat niet over de weg gaat, per maand. -->
        <p class="mb-1.5 mt-3 truncate text-[11px] leading-4 text-gray-600">
            <span class="font-medium text-gray-900">Zee + lucht per maand</span>
            <template v-for="deel in s.lezing" :key="deel">
                <span class="text-gray-300"> · </span>{{ deel }}
            </template>
        </p>
        <div :class="heightClass">
            <Chart type="bar" :data="chartData" :options="chartOptions" class="h-full w-full" />
        </div>
        <div class="mt-1 flex items-center justify-between gap-2 text-[9px] text-gray-500">
            <span>{{ s.startLabel }}</span>
            <span class="flex items-center gap-2.5">
                <span class="flex items-center gap-1">
                    <span class="inline-block h-1.5 w-1.5 rounded-sm" :style="{ background: zee.kleur }" />
                    zee
                </span>
                <span class="flex items-center gap-1">
                    <span class="inline-block h-1.5 w-1.5 rounded-sm" :style="{ background: lucht.kleur }" />
                    lucht
                </span>
                <span v-if="s.gemiddelde != null" class="flex items-center gap-1">
                    <span class="inline-block w-3 border-t border-dashed border-gray-500" />
                    gem.
                </span>
                <span v-if="s.open.some(Boolean)" class="flex items-center gap-1">
                    <span class="inline-block h-1.5 w-1.5 rounded-sm border border-gray-500" />
                    voorlopig
                </span>
            </span>
            <span>{{ s.eindLabel }}</span>
        </div>
    </div>
</template>
