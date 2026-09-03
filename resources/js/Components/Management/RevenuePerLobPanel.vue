<script setup>
import { KPI_STATUS, STATUS_LABELS, STATUS_TAG_SEVERITY } from '@/config/mtKpiFramework';
import Card from 'primevue/card';
import Chart from 'primevue/chart';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Tag from 'primevue/tag';
import { computed } from 'vue';

const props = defineProps({
    panel: { type: Object, required: true },
    embedded: { type: Boolean, default: false },
    trendOnly: { type: Boolean, default: false },
    showTitle: { type: Boolean, default: true },
});

const lobColors = {
    AWC: '#0ea5e9',
    AFC: '#ff7020',
    ACC: '#6366f1',
};

const extraColors = [
    '#10b981',
    '#f59e0b',
    '#ec4899',
    '#8b5cf6',
    '#14b8a6',
    '#f97316',
    '#64748b',
    '#84cc16',
];

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

const isLive = computed(() => props.panel.status === KPI_STATUS.LIVE);

const statusLabel = computed(
    () => STATUS_LABELS[props.panel.status] ?? props.panel.status,
);
const statusSeverity = computed(
    () => STATUS_TAG_SEVERITY[props.panel.status] ?? 'secondary',
);

const cardPt = {
    root: { class: 'border border-gray-100 shadow-sm' },
    body: { class: '!p-0' },
    content: { class: '!p-5' },
};

function barColor(lob, index = 0) {
    const key = String(lob ?? '').toUpperCase();
    if (lobColors[key]) return lobColors[key];
    return extraColors[index % extraColors.length];
}

function monthLabel(row) {
    const m = Number(row?.month);
    if (m >= 1 && m <= 12) {
        return monthNames[m];
    }
    const bp = String(row?.book_period ?? '');
    if (bp.length >= 2) {
        const tail = Number(bp.slice(-2));
        if (tail >= 1 && tail <= 12) {
            return monthNames[tail];
        }
    }
    return bp || '—';
}

function sortedMonths(months) {
    return [...(months ?? [])].sort(
        (a, b) => Number(a.book_period) - Number(b.book_period),
    );
}

const monthlySeries = computed(() => {
    const entries = props.panel.monthlyByLob ?? [];
    return entries
        .map((e) => ({
            ...e,
            total: (e.months ?? []).reduce(
                (s, m) => s + Number(m.omzet ?? 0),
                0,
            ),
        }))
        .filter((e) => e.total > 0)
        .sort((a, b) => b.total - a.total)
        .slice(0, 10);
});

const hasMonthlyTrend = computed(() => monthlySeries.value.length > 0);

const allMonthLabels = computed(() => {
    const labels = new Set();
    for (const ent of monthlySeries.value) {
        for (const row of sortedMonths(ent.months)) {
            labels.add(monthLabel(row));
        }
    }
    const order = monthNames.filter(Boolean);
    return [...labels].sort(
        (a, b) => order.indexOf(a) - order.indexOf(b),
    );
});

const monthlyTrendChart = computed(() => {
    const labels = allMonthLabels.value;
    const datasets = monthlySeries.value.map((ent, i) => {
        const byLabel = Object.fromEntries(
            sortedMonths(ent.months).map((m) => [
                monthLabel(m),
                Number(m.omzet ?? 0),
            ]),
        );
        const color = barColor(ent.lob, i);
        return {
            label: ent.lob,
            data: labels.map((l) => byLabel[l] ?? null),
            borderColor: color,
            backgroundColor: color,
            tension: 0.35,
            fill: false,
            spanGaps: true,
        };
    });

    return {
        labels: labels.length ? labels : ['—'],
        datasets: datasets.length
            ? datasets
            : [{ label: 'Omzet', data: [0], borderColor: '#1e3a5f' }],
    };
});

const monthlyTrendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'bottom' },
        tooltip: {
            callbacks: {
                label(ctx) {
                    const v = ctx.parsed.y;
                    if (v == null || Number.isNaN(v)) {
                        return `${ctx.dataset.label}: —`;
                    }
                    if (Math.abs(v) >= 1_000_000) {
                        return `${ctx.dataset.label}: €${(v / 1_000_000).toFixed(2)}M`;
                    }
                    if (Math.abs(v) >= 1_000) {
                        return `${ctx.dataset.label}: €${Math.round(v / 1_000)}K`;
                    }
                    return `${ctx.dataset.label}: €${Math.round(v).toLocaleString('nl-NL')}`;
                },
            },
        },
    },
    scales: {
        y: {
            beginAtZero: true,
            ticks: {
                callback(v) {
                    if (Math.abs(v) >= 1_000_000) {
                        return `€${(v / 1_000_000).toFixed(1)}M`;
                    }
                    if (Math.abs(v) >= 1_000) {
                        return `€${Math.round(v / 1_000)}K`;
                    }
                    return `€${v}`;
                },
            },
        },
    },
};

const chartData = computed(() => {
    const rows = props.panel.rows ?? [];
    return {
        labels: rows.map((r) => r.lob),
        datasets: [
            {
                label: 'Omzet',
                data: rows.map((r) => r.omzet),
                backgroundColor: rows.map((r, i) => barColor(r.lob, i)),
                borderRadius: 4,
                barThickness: 22,
            },
        ],
    };
});

const chartOptions = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            callbacks: {
                label(ctx) {
                    const row = props.panel.rows?.[ctx.dataIndex];
                    if (!row) return '';
                    const parts = [
                        `€${Number(row.omzet).toLocaleString('nl-NL')}`,
                        `${row.aandeel_pct}%`,
                    ];
                    if (row.delta_fmt) parts.push(`YoY ${row.delta_fmt}`);
                    return parts.join(' · ');
                },
            },
        },
    },
    scales: {
        x: {
            beginAtZero: true,
            ticks: {
                callback(v) {
                    if (Math.abs(v) >= 1_000_000)
                        return `€${(v / 1_000_000).toFixed(1)}M`;
                    if (Math.abs(v) >= 1_000)
                        return `€${Math.round(v / 1_000)}K`;
                    return `€${v}`;
                },
            },
        },
        y: { grid: { display: false } },
    },
};

const hasPeriodData = computed(
    () => isLive.value && (props.panel.rows?.length ?? 0) > 0,
);

const showContent = computed(() => {
    if (props.trendOnly) {
        return hasMonthlyTrend.value;
    }
    return hasPeriodData.value || hasMonthlyTrend.value;
});
</script>

<template>
    <Card v-if="!embedded" :pt="cardPt">
        <template #content>
            <div
                class="mb-4 flex flex-wrap items-start justify-between gap-3"
            >
                <div v-if="showTitle">
                    <p
                        class="text-[10px] font-semibold uppercase tracking-wider text-[#ff7020]"
                    >
                        Groei
                    </p>
                    <h3 class="text-sm font-semibold text-gray-900">
                        Revenue per Line of Business
                    </h3>
                    <p class="mt-1 text-xs text-gray-500">
                        {{ panel.lobField }}
                        <span v-if="panel.periodLabel">
                            · {{ panel.periodLabel }}</span
                        >
                    </p>
                </div>
                <Tag
                    :value="statusLabel"
                    :severity="statusSeverity"
                    class="shrink-0 !text-[10px]"
                />
            </div>

            <template v-if="showContent">
                <div
                    v-if="hasPeriodData && !trendOnly"
                    class="mb-4 flex flex-wrap items-baseline gap-x-6 gap-y-1 border-b border-gray-100 pb-4"
                >
                    <div>
                        <p class="text-xs text-gray-500">Totaal periode</p>
                        <p class="text-2xl font-bold text-gray-900">
                            {{ panel.totaalFmt }}
                        </p>
                        <p
                            v-if="panel.deltaTotaalFmt"
                            class="text-sm font-medium"
                            :class="
                                panel.deltaTotaalPositive
                                    ? 'text-emerald-600'
                                    : 'text-red-600'
                            "
                        >
                            {{ panel.deltaTotaalFmt }}
                            <span class="font-normal text-gray-400"
                                >vs {{ panel.totaalVorigFmt }}</span
                            >
                        </p>
                    </div>
                </div>

                <div
                    v-if="hasMonthlyTrend"
                    class="mb-6 rounded-lg border border-gray-100 bg-white p-4"
                >
                    <h3 class="mb-3 text-sm font-semibold text-gray-800">
                        Omzet maandtrend per LOB
                    </h3>
                    <div class="h-56 min-h-[14rem]">
                        <Chart
                            type="line"
                            :data="monthlyTrendChart"
                            :options="monthlyTrendOptions"
                            class="h-full w-full"
                        />
                    </div>
                </div>

                <div
                    v-if="hasPeriodData && !trendOnly"
                    class="grid grid-cols-1 gap-6 lg:grid-cols-2"
                >
                    <div class="h-52 min-h-[12rem] lg:min-h-[14rem]">
                        <Chart
                            type="bar"
                            :data="chartData"
                            :options="chartOptions"
                            class="h-full w-full"
                        />
                    </div>
                    <DataTable
                        :value="panel.rows"
                        striped-rows
                        show-gridlines
                        class="p-datatable-sm text-sm"
                        :empty-message="'Geen LOB-data.'"
                    >
                        <Column field="lob" header="LOB">
                            <template #body="{ data }">
                                <span
                                    class="inline-flex items-center gap-2 font-medium text-gray-900"
                                >
                                    <span
                                        class="size-2 shrink-0 rounded-full"
                                        :style="{
                                            backgroundColor: barColor(data.lob),
                                        }"
                                    />
                                    {{ data.lob }}
                                </span>
                            </template>
                        </Column>
                        <Column field="omzet_fmt" header="Omzet" />
                        <Column field="aandeel_pct_fmt" header="Aandeel" />
                        <Column field="omzet_vorig_fmt" header="Vorig jaar" />
                        <Column field="delta_fmt" header="Δ%">
                            <template #body="{ data }">
                                <span
                                    v-if="data.delta_fmt"
                                    class="font-medium"
                                    :class="
                                        data.delta_positive
                                            ? 'text-emerald-600'
                                            : 'text-red-600'
                                    "
                                >
                                    {{ data.delta_fmt }}
                                </span>
                                <span v-else class="text-gray-400">—</span>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </template>

            <div
                v-else
                class="rounded-md border border-dashed border-gray-200 bg-gray-50/80 px-4 py-6 text-center"
            >
                <p class="text-sm font-medium text-gray-500">
                    {{
                        trendOnly
                            ? 'Geen maandtrend beschikbaar'
                            : 'Geen LOB-uitsplitsing beschikbaar'
                    }}
                </p>
                <p v-if="panel.note" class="mt-1 text-xs text-gray-500">
                    {{ panel.note }}
                </p>
                <p
                    v-else-if="trendOnly && hasPeriodData"
                    class="mt-1 text-xs text-gray-500"
                >
                    Deploy peliqan_mt_api_handler voor omzet maandtrend per LOB.
                </p>
            </div>
        </template>
    </Card>

    <div v-else>
        <div
            class="flex flex-wrap items-start justify-between gap-3"
            :class="showTitle ? 'mb-4' : 'mb-3'"
        >
            <div v-if="showTitle">
                <p
                    class="text-[10px] font-semibold uppercase tracking-wider text-[#ff7020]"
                >
                    Groei
                </p>
                <h4 class="text-sm font-semibold text-gray-800">
                    Revenue per Line of Business
                </h4>
                <p class="mt-0.5 text-xs text-gray-500">
                    {{ panel.lobField }}
                    <span v-if="panel.periodLabel">
                        · {{ panel.periodLabel }}</span
                    >
                </p>
            </div>
            <Tag
                :value="statusLabel"
                :severity="statusSeverity"
                class="shrink-0 !text-[10px]"
            />
        </div>

        <template v-if="showContent">
            <div
                v-if="hasPeriodData && !trendOnly"
                class="mb-4 flex flex-wrap items-baseline gap-x-6 gap-y-1 border-b border-gray-100 pb-4"
            >
                <div>
                    <p class="text-xs text-gray-500">Totaal periode</p>
                    <p class="text-2xl font-bold text-gray-900">
                        {{ panel.totaalFmt }}
                    </p>
                    <p
                        v-if="panel.deltaTotaalFmt"
                        class="text-sm font-medium"
                        :class="
                            panel.deltaTotaalPositive
                                ? 'text-emerald-600'
                                : 'text-red-600'
                        "
                    >
                        {{ panel.deltaTotaalFmt }}
                        <span class="font-normal text-gray-400"
                            >vs {{ panel.totaalVorigFmt }}</span
                        >
                    </p>
                </div>
            </div>

            <div
                v-if="hasMonthlyTrend"
                :class="
                    trendOnly
                        ? 'mt-4 h-52 min-h-[12rem]'
                        : 'mb-6 rounded-lg border border-gray-100 bg-white p-4'
                "
            >
                <h3
                    v-if="!trendOnly"
                    class="mb-3 text-sm font-semibold text-gray-800"
                >
                    Omzet maandtrend per LOB
                </h3>
                <div :class="trendOnly ? 'h-full' : 'h-56 min-h-[14rem]'">
                    <Chart
                        type="line"
                        :data="monthlyTrendChart"
                        :options="monthlyTrendOptions"
                        class="h-full w-full"
                    />
                </div>
            </div>

            <div
                v-if="hasPeriodData && !trendOnly"
                class="grid grid-cols-1 gap-6 lg:grid-cols-2"
            >
                <div class="h-52 min-h-[12rem] lg:min-h-[14rem]">
                    <Chart
                        type="bar"
                        :data="chartData"
                        :options="chartOptions"
                        class="h-full w-full"
                    />
                </div>
                <DataTable
                    :value="panel.rows"
                    striped-rows
                    show-gridlines
                    class="p-datatable-sm text-sm"
                    :empty-message="'Geen LOB-data.'"
                >
                    <Column field="lob" header="LOB">
                        <template #body="{ data }">
                            <span
                                class="inline-flex items-center gap-2 font-medium text-gray-900"
                            >
                                <span
                                    class="size-2 shrink-0 rounded-full"
                                    :style="{
                                        backgroundColor: barColor(data.lob),
                                    }"
                                />
                                {{ data.lob }}
                            </span>
                        </template>
                    </Column>
                    <Column field="omzet_fmt" header="Omzet" />
                    <Column field="aandeel_pct_fmt" header="Aandeel" />
                    <Column field="omzet_vorig_fmt" header="Vorig jaar" />
                    <Column field="delta_fmt" header="Δ%">
                        <template #body="{ data }">
                            <span
                                v-if="data.delta_fmt"
                                class="font-medium"
                                :class="
                                    data.delta_positive
                                        ? 'text-emerald-600'
                                        : 'text-red-600'
                                "
                            >
                                {{ data.delta_fmt }}
                            </span>
                            <span v-else class="text-gray-400">—</span>
                        </template>
                    </Column>
                </DataTable>
            </div>
        </template>

        <div
            v-else
            class="rounded-md border border-dashed border-gray-200 bg-gray-50/80 px-4 py-6 text-center"
        >
            <p class="text-sm font-medium text-gray-500">
                {{
                    trendOnly
                        ? 'Geen maandtrend beschikbaar'
                        : 'Geen LOB-uitsplitsing beschikbaar'
                }}
            </p>
            <p v-if="panel.note" class="mt-1 text-xs text-gray-500">
                {{ panel.note }}
            </p>
            <p
                v-else-if="trendOnly && hasPeriodData"
                class="mt-1 text-xs text-gray-500"
            >
                Deploy peliqan_mt_api_handler voor omzet maandtrend per LOB.
            </p>
        </div>
    </div>
</template>
