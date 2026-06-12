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
        required: true,
    },
    delta: {
        type: String,
        default: '',
    },
    deltaPositive: {
        type: Boolean,
        default: true,
    },
    footer: {
        type: String,
        default: '',
    },
    sparkData: {
        type: Array,
        required: true,
    },
    tagLabel: {
        type: String,
        default: '',
    },
    tagVariant: {
        type: String,
        default: 'sky',
        validator: (v) => ['sky', 'orange'].includes(v),
    },
    clickable: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(['click']);

function onActivate() {
    if (props.clickable) emit('click');
}

function onKeydown(e) {
    if (!props.clickable) return;
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        emit('click');
    }
}

const brandBlue = '#1e3a5f';

const chartData = computed(() => ({
    labels: props.sparkData.map((_, i) => i),
    datasets: [
        {
            data: props.sparkData,
            borderColor: brandBlue,
            borderWidth: 2,
            fill: false,
            tension: 0.35,
            pointRadius: 0,
            pointHoverRadius: 0,
        },
    ],
}));

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

const tagClass = computed(() => {
    const map = {
        sky: 'rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-sky-100 text-sky-800',
        orange: 'rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-orange-100 text-orange-900',
    };
    return map[props.tagVariant] ?? map.sky;
});
</script>

<template>
    <Card
        :pt="cardPt"
        :class="
            clickable
                ? 'cursor-pointer transition hover:border-[#ff7020]/40 hover:shadow-md focus-within:ring-2 focus-within:ring-[#ff7020]/30'
                : ''
        "
        :role="clickable ? 'button' : undefined"
        :tabindex="clickable ? 0 : undefined"
        @click="onActivate"
        @keydown="onKeydown"
    >
        <template #content>
            <div class="flex items-start justify-between gap-2">
                <div class="flex items-center gap-2 min-w-0">
                    <h3 class="text-sm font-semibold leading-tight text-gray-900">
                        {{ title }}
                    </h3>
                    <button
                        type="button"
                        class="shrink-0 text-gray-400 transition hover:text-gray-600"
                        aria-label="Info"
                        @click.stop
                    >
                        <i class="pi pi-info-circle text-sm" />
                    </button>
                </div>
                <span v-if="tagLabel" :class="tagClass">{{ tagLabel }}</span>
            </div>

            <div>
                <p class="text-3xl font-bold tracking-tight text-gray-900">
                    {{ value }}
                </p>
                <p
                    v-if="delta"
                    class="mt-1 text-sm font-medium"
                    :class="
                        deltaPositive ? 'text-emerald-600' : 'text-red-600'
                    "
                >
                    {{ delta }}
                </p>
            </div>

            <div class="h-14 w-full shrink-0">
                <Chart
                    type="line"
                    :data="chartData"
                    :options="chartOptions"
                    class="!h-full !max-h-14 w-full"
                />
            </div>

            <div
                class="mt-auto border-t border-gray-100 pt-3"
            >
                <p
                    v-if="footer"
                    class="text-xs text-gray-500"
                >
                    {{ footer }}
                </p>
                <p
                    v-if="clickable"
                    class="mt-1 flex items-center gap-1 text-xs font-semibold text-[#ff7020]"
                >
                    Bekijk detail
                    <i class="pi pi-arrow-right text-[10px]" />
                </p>
            </div>
        </template>
    </Card>
</template>
