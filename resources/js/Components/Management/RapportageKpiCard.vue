<script setup>
import Card from 'primevue/card';
import Chart from 'primevue/chart';
import { computed } from 'vue';

const props = defineProps({
    title: {
        type: String,
        required: true,
    },
    value: {
        type: String,
        default: '',
    },
    placeholder: {
        type: Boolean,
        default: false,
    },
    sublabel: {
        type: String,
        default: '',
    },
    sublabelTone: {
        type: String,
        default: 'neutral',
        validator: (v) => ['neutral', 'positive', 'negative'].includes(v),
    },
    sparkData: {
        type: Array,
        default: null,
    },
    sparkDotted: {
        type: Boolean,
        default: false,
    },
    footerInitial: {
        type: String,
        default: '',
    },
    footerName: {
        type: String,
        default: '',
    },
    footerSource: {
        type: String,
        default: '',
    },
    footerFrequency: {
        type: String,
        default: '',
    },
});

const lineColor = '#111827';
const accentOrange = '#ff7020';

const sublabelClass = computed(() => {
    const map = {
        neutral: 'text-gray-500',
        positive: 'text-emerald-600',
        negative: 'text-red-600',
    };
    return map[props.sublabelTone] ?? map.neutral;
});

const hasSpark = computed(
    () =>
        !props.placeholder &&
        Array.isArray(props.sparkData) &&
        props.sparkData.length > 0,
);

const chartData = computed(() => {
    const data = props.sparkData ?? [];
    return {
        labels: data.map((_, i) => i),
        datasets: [
            {
                data,
                borderColor: lineColor,
                borderWidth: 2,
                borderDash: props.sparkDotted ? [4, 4] : [],
                fill: false,
                tension: 0.35,
                pointRadius: (ctx) =>
                    ctx.dataIndex === data.length - 1 ? 4 : 0,
                pointBackgroundColor: (ctx) =>
                    ctx.dataIndex === data.length - 1
                        ? accentOrange
                        : 'transparent',
                pointBorderColor: (ctx) =>
                    ctx.dataIndex === data.length - 1 ? accentOrange : 'transparent',
                pointBorderWidth: (ctx) =>
                    ctx.dataIndex === data.length - 1 ? 2 : 0,
                pointHoverRadius: 0,
            },
        ],
    };
});

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: { enabled: false },
    },
    scales: {
        x: { display: false },
        y: { display: false },
    },
};

const cardPt = {
    root: {
        class: 'border border-gray-100 shadow-sm overflow-hidden h-full flex flex-col',
    },
    body: { class: '!p-0 flex flex-col flex-1' },
    content: { class: '!p-5 flex flex-col flex-1 gap-3' },
};

const footerMeta = computed(() =>
    [props.footerSource, props.footerFrequency].filter(Boolean).join(' · '),
);
</script>

<template>
    <Card :pt="cardPt">
        <template #content>
            <div class="flex items-start justify-between gap-2">
                <div class="flex min-w-0 items-center gap-2">
                    <h3 class="text-sm font-semibold leading-tight text-gray-900">
                        {{ title }}
                    </h3>
                    <button
                        type="button"
                        class="shrink-0 text-gray-400 transition hover:text-gray-600"
                        aria-label="Info"
                    >
                        <i class="pi pi-info-circle text-sm" />
                    </button>
                </div>
            </div>

            <div class="flex min-h-[5.5rem] items-center gap-3">
                <div class="min-w-0 flex-1">
                    <template v-if="placeholder">
                        <p class="text-sm font-medium text-gray-400">
                            Nog geen data
                        </p>
                        <p class="mt-1 text-xs text-gray-400">
                            Selecteer een periode
                        </p>
                    </template>
                    <template v-else>
                        <p class="text-3xl font-bold tracking-tight text-gray-900">
                            {{ value }}
                        </p>
                        <p
                            v-if="sublabel"
                            class="mt-1 text-sm font-medium"
                            :class="sublabelClass"
                        >
                            {{ sublabel }}
                        </p>
                    </template>
                </div>

                <div
                    v-if="hasSpark"
                    class="h-16 w-[6.5rem] shrink-0"
                >
                    <Chart
                        type="line"
                        :data="chartData"
                        :options="chartOptions"
                        class="!h-full w-full"
                    />
                </div>
                <div
                    v-else-if="!placeholder"
                    class="flex h-16 w-[6.5rem] shrink-0 items-center justify-center rounded border border-dashed border-gray-200 bg-gray-50"
                >
                    <span class="text-[10px] text-gray-400">—</span>
                </div>
            </div>

            <div
                v-if="footerInitial || footerName || footerMeta"
                class="mt-auto flex items-center gap-2 border-t border-gray-100 pt-3"
            >
                <span
                    v-if="footerInitial"
                    class="flex size-7 shrink-0 items-center justify-center rounded-full bg-gray-200 text-xs font-semibold text-gray-700"
                >
                    {{ footerInitial }}
                </span>
                <p class="min-w-0 text-xs leading-snug text-gray-500">
                    <span v-if="footerName" class="font-medium text-gray-700">{{
                        footerName
                    }}</span>
                    <template v-if="footerMeta">
                        <span v-if="footerName"> · </span>{{ footerMeta }}
                    </template>
                </p>
            </div>
        </template>
    </Card>
</template>
