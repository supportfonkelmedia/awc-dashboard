<script setup>
import { KPI_STATUS, STATUS_LABELS, STATUS_TAG_SEVERITY } from '@/config/mtKpiFramework';
import Card from 'primevue/card';
import Chart from 'primevue/chart';
import Message from 'primevue/message';
import Tag from 'primevue/tag';
import { computed } from 'vue';

const props = defineProps({
    panel: { type: Object, required: true },
    embedded: { type: Boolean, default: false },
});

const monthNames = [
    '',
    'Jan',
    'Feb',
    'Mrt',
    'Apr',
    'Mei',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Okt',
    'Nov',
    'Dec',
];

const brandBlue = '#1e3a5f';

const statusLabel = computed(
    () => STATUS_LABELS[props.panel.status] ?? props.panel.status,
);
const statusSeverity = computed(
    () => STATUS_TAG_SEVERITY[props.panel.status] ?? 'secondary',
);

const isLive = computed(() => props.panel.status === KPI_STATUS.LIVE);

const cardPt = {
    root: { class: 'border border-gray-100 shadow-sm' },
    body: { class: '!p-0' },
    content: { class: '!p-5' },
};

function fmtPct(v) {
    if (v == null || Number.isNaN(Number(v))) return '—';
    return `${Number(v).toLocaleString('nl-NL', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
    })}%`;
}

function monthLabel(m) {
    const n = Number(m);
    return n >= 1 && n <= 12 ? monthNames[n] : '—';
}

const trendChart = computed(() => {
    const rows = props.panel.monthly ?? [];
    const labels = rows.map((r) => {
        const base = monthLabel(r.month);
        return r.preliminary ? `${base}*` : base;
    });
    return {
        labels,
        datasets: [
            {
                label: '% binnen 24 uur',
                data: rows.map((r) => r.pct_within_24h),
                borderColor: brandBlue,
                backgroundColor: brandBlue,
                tension: 0.35,
                pointRadius: 4,
                fill: false,
            },
        ],
    };
});

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            callbacks: {
                label(ctx) {
                    const row = props.panel.monthly?.[ctx.dataIndex];
                    const pct = ctx.parsed.y;
                    if (row == null) return `${pct}%`;
                    return `${pct}% (${row.within_24h}/${row.orders} orders)`;
                },
            },
        },
    },
    scales: {
        y: {
            min: 0,
            max: 100,
            ticks: {
                callback: (v) => `${v}%`,
            },
        },
    },
};

const hasTrend = computed(() => (props.panel.monthly ?? []).length > 0);
</script>

<template>
    <div class="space-y-4">
        <div
            v-if="!embedded"
            class="flex flex-wrap items-center justify-between gap-2"
        >
            <div>
                <p class="text-sm font-semibold text-gray-800">
                    Dock-to-Stock
                </p>
                <p class="text-xs text-gray-500">
                    Operationele AWC-tegel · norm binnen 24 uur na lossen
                </p>
            </div>
            <Tag
                :value="statusLabel"
                :severity="statusSeverity"
                class="text-xs"
            />
        </div>

        <Message
            v-if="panel.note && !isLive"
            severity="info"
            :closable="false"
            class="text-sm"
        >
            {{ panel.note }}
        </Message>

        <Message
            v-if="panel.preliminary && isLive"
            severity="warn"
            :closable="false"
            class="text-sm"
        >
            Lopende maand is voorlopig — trage orders zijn nog niet afgerond.
        </Message>

        <div
            v-if="isLive"
            class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
            <Card :pt="cardPt">
                <template #content>
                    <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Binnen 24 uur
                    </p>
                    <p class="mt-1 text-2xl font-bold text-gray-900">
                        {{ fmtPct(panel.pctWithin24h) }}
                    </p>
                    <p class="mt-1 text-xs text-gray-500">
                        {{ panel.within24h }}/{{ panel.measurableOrders }} orders
                        · {{ panel.periodLabel }}
                    </p>
                </template>
            </Card>

            <Card :pt="cardPt">
                <template #content>
                    <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Mediaan doorlooptijd
                    </p>
                    <p class="mt-1 text-2xl font-bold text-gray-900">
                        {{
                            panel.medianHours != null
                                ? `${panel.medianHours} uur`
                                : '—'
                        }}
                    </p>
                    <p class="mt-1 text-xs text-gray-500">
                        Losmoment → status 30 (niet gemiddelde)
                    </p>
                </template>
            </Card>

            <Card :pt="cardPt">
                <template #content>
                    <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Dekking
                    </p>
                    <p class="mt-1 text-2xl font-bold text-gray-900">
                        {{ fmtPct(panel.coveragePct) }}
                    </p>
                    <p class="mt-1 text-xs text-gray-500">
                        {{ panel.measurableOrders }}/{{ panel.totalUnloaded }}
                        geloste inbounds met verplaatsing
                    </p>
                </template>
            </Card>

            <Card :pt="cardPt">
                <template #content>
                    <p class="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Norm
                    </p>
                    <p class="mt-1 text-2xl font-bold text-gray-900">
                        ≤ {{ panel.normHours ?? 24 }} uur
                    </p>
                    <p class="mt-1 text-xs text-gray-500">
                        Brief Fonkel deel 3 · 7T Spare_Orders
                    </p>
                </template>
            </Card>
        </div>

        <Card v-if="hasTrend" :pt="cardPt">
            <template #content>
                <p class="mb-3 text-sm font-semibold text-gray-800">
                    Maandtrend {{ panel.year }}
                    <span class="font-normal text-gray-500"
                        >(* = voorlopige maand)</span
                    >
                </p>
                <div class="h-56">
                    <Chart
                        type="line"
                        :data="trendChart"
                        :options="chartOptions"
                        class="h-full w-full"
                    />
                </div>
            </template>
        </Card>
    </div>
</template>
