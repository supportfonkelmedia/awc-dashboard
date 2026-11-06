<script setup>
import Chart from 'primevue/chart';
import { computed } from 'vue';
import { formatKpiValue } from '@/utils/kpiFormat';

const props = defineProps({
    series: {
        type: Array,
        default: () => [],
    },
    /** KPI eenheid for tooltip formatting */
    eenheid: {
        type: String,
        default: 'ratio',
    },
    heightClass: {
        type: String,
        default: 'h-14',
    },
    emptyText: {
        type: String,
        default: 'Nog geen maandhistorie',
    },
});

const colors = ['#2563eb', '#0ea5e9', '#6366f1', '#14b8a6'];

const chartData = computed(() => {
    const datasets = props.series.map((s, idx) => {
        const points = s.points ?? [];
        const data = points.map((p) =>
            p.waarde != null ? Number(p.waarde) : null,
        );
        const borderColor = colors[idx % colors.length];
        const segment = [];
        for (let i = 0; i < points.length - 1; i++) {
            const st = String(points[i + 1]?.status ?? 'definitief');
            segment.push(
                st === 'voorlopig' || st === 'onvolledig' ? [5, 5] : undefined,
            );
        }

        const lastIdx = points.length - 1;
        const isOpen = (p) => {
            const st = String(p?.status ?? 'definitief');

            return st === 'voorlopig' || st === 'onvolledig';
        };

        return {
            label: s.serie || 'Trend',
            data,
            borderColor,
            borderWidth: 1.5,
            fill: false,
            tension: 0.3,
            // Mockup: dot on the last point (hollow when the period is still open).
            pointRadius: points.map((p, i) => (i === lastIdx || isOpen(p) ? 2.5 : 0)),
            pointHoverRadius: 3,
            pointBackgroundColor: points.map((p) =>
                isOpen(p) ? '#fff' : borderColor,
            ),
            pointBorderColor: borderColor,
            pointBorderWidth: 1.5,
            spanGaps: false,
            segment: {
                borderDash: (ctx) => segment[ctx.p0DataIndex] ?? undefined,
            },
        };
    });

    const maxLen = Math.max(0, ...datasets.map((d) => d.data.length));
    const labels = Array.from({ length: maxLen }, (_, i) => i);

    return { labels, datasets };
});

const hasData = computed(() =>
    props.series.some((s) => (s.points?.length ?? 0) > 0),
);

const periodFmt = new Intl.DateTimeFormat('nl-NL', {
    month: 'short',
    year: '2-digit',
    timeZone: 'UTC',
});

/**
 * @param {Record<string, unknown>|undefined} point
 */
function periodLabel(point) {
    if (!point?.periode) {
        return '';
    }
    const d = new Date(String(point.periode));
    if (Number.isNaN(d.getTime())) {
        return String(point.periode);
    }

    return periodFmt.format(d).replace('.', '');
}

const axisLabels = computed(() => {
    const first = props.series.find((s) => (s.points?.length ?? 0) > 0);
    if (!first) {
        return { start: '', end: '' };
    }
    const pts = first.points;
    const last = pts[pts.length - 1];
    const st = String(last?.status ?? 'definitief');
    const endLabel = periodLabel(last);

    return {
        start: periodLabel(pts[0]),
        end: st === 'voorlopig' || st === 'onvolledig' ? `${endLabel} (lopend)` : endLabel,
    };
});

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    layout: { padding: { left: 3, right: 4, top: 4, bottom: 3 } },
    plugins: {
        legend: { display: props.series.length > 1 },
        tooltip: {
            callbacks: {
                label(ctx) {
                    const v = ctx.raw;
                    if (v == null) {
                        return '';
                    }

                    return formatKpiValue(props.eenheid, v) || String(v);
                },
            },
        },
    },
    scales: {
        x: { display: false },
        y: { display: false },
    },
}));
</script>

<template>
    <div v-if="hasData" class="w-full">
        <div :class="heightClass">
            <Chart
                type="line"
                :data="chartData"
                :options="chartOptions"
                class="h-full w-full"
            />
        </div>
        <div class="mt-1 flex justify-between text-[9px] text-gray-500">
            <span>{{ axisLabels.start }}</span>
            <span>{{ axisLabels.end }}</span>
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
