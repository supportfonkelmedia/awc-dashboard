<script setup>
import { KPI_STATUS, STATUS_LABELS, STATUS_TAG_SEVERITY } from '@/config/mtKpiFramework';
import Card from 'primevue/card';
import Chart from 'primevue/chart';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Message from 'primevue/message';
import Tag from 'primevue/tag';
import { computed } from 'vue';

const props = defineProps({
    panel: { type: Object, required: true },
    compact: { type: Boolean, default: false },
    embedded: { type: Boolean, default: false },
    showPartialWage: { type: Boolean, default: true },
});

const entityColors = {
    AWC: '#0ea5e9',
    AFC: '#ff7020',
    ACC: '#6366f1',
};

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

function entityColor(label) {
    return entityColors[String(label ?? '').toUpperCase()] ?? '#1e3a5f';
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

const entitiesWithMonths = computed(() =>
    (props.panel.entities ?? []).filter((e) => (e.months ?? []).length),
);

const hasSummary = computed(
    () =>
        props.panel.totals?.kpi != null ||
        props.panel.entities?.some((e) => e.kpi != null),
);

const isLive = computed(
    () =>
        props.panel.status === KPI_STATUS.LIVE &&
        (hasSummary.value || entitiesWithMonths.value.length > 0),
);

const allMonthLabels = computed(() => {
    const labels = new Set();
    for (const ent of props.panel.entities ?? []) {
        for (const row of sortedMonths(ent.months)) {
            labels.add(monthLabel(row));
        }
    }
    const order = monthNames.filter(Boolean);
    return [...labels].sort(
        (a, b) => order.indexOf(a) - order.indexOf(b),
    );
});

const kpiTrendChart = computed(() => {
    const labels = allMonthLabels.value;
    const datasets = (props.panel.entities ?? [])
        .filter((e) => (e.months ?? []).length)
        .map((ent) => {
            const byLabel = Object.fromEntries(
                sortedMonths(ent.months).map((m) => [monthLabel(m), m.kpi]),
            );
            return {
                label: ent.label,
                data: labels.map((l) => byLabel[l] ?? null),
                borderColor: entityColor(ent.label),
                backgroundColor: entityColor(ent.label),
                tension: 0.35,
                fill: false,
                spanGaps: true,
            };
        });

    return {
        labels: labels.length ? labels : ['—'],
        datasets: datasets.length
            ? datasets
            : [{ label: 'KPI', data: [0], borderColor: '#1e3a5f' }],
    };
});

const kpiTrendOptions = {
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
                    return `${ctx.dataset.label}: ${Number(v).toFixed(2).replace('.', ',')}×`;
                },
            },
        },
    },
    scales: {
        y: {
            beginAtZero: true,
            ticks: {
                callback(v) {
                    return `${Number(v).toFixed(1).replace('.', ',')}×`;
                },
            },
        },
    },
};

function entityMargeChart(ent) {
    const rows = sortedMonths(ent.months);
    const labels = rows.map((m) => monthLabel(m));
    return {
        labels: labels.length ? labels : ['—'],
        datasets: [
            {
                label: 'Brutomarge',
                data: rows.map((m) => Number(m.bruto_marge ?? 0)),
                borderColor: entityColor(ent.label),
                backgroundColor: `${entityColor(ent.label)}33`,
                tension: 0.35,
                fill: true,
            },
            {
                label: 'Loonkosten',
                data: rows.map((m) => Number(m.loonkosten ?? 0)),
                borderColor: '#94a3b8',
                backgroundColor: '#94a3b833',
                tension: 0.35,
                fill: false,
            },
        ],
    };
}

const margeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'bottom' },
        tooltip: {
            callbacks: {
                label(ctx) {
                    const v = ctx.parsed.y;
                    if (v == null) return '';
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

const showPartialBlock = computed(
    () =>
        props.showPartialWage &&
        props.panel.entities?.some(
            (e) =>
                ['pgl1', 'acco'].includes(e.admin_code) &&
                Object.values(e.partial_wage ?? {}).some((v) => v > 0),
        ),
);
</script>

<template>
    <div>
        <div
            v-if="embedded"
            class="flex flex-wrap items-start justify-between gap-3"
        >
            <div>
                <p
                    class="text-[10px] font-semibold uppercase tracking-wider text-[#ff7020]"
                >
                    Efficiëntie
                </p>
                <h4 class="text-sm font-semibold text-gray-800">
                    Bruto marge per loonkosten
                </h4>
                <p v-if="panel.periodLabel" class="mt-0.5 text-xs text-gray-500">
                    {{ panel.periodLabel }}
                </p>
            </div>
            <Tag
                :value="statusLabel"
                :severity="statusSeverity"
                class="shrink-0 !text-[10px]"
            />
        </div>

        <div
            v-else-if="!compact"
            class="mb-4 flex flex-wrap items-start justify-between gap-3"
        >
            <Tag
                :value="statusLabel"
                :severity="statusSeverity"
                class="shrink-0 !text-[10px]"
            />
        </div>

        <div
            v-if="!embedded && (hasSummary || panel.totals)"
            class="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
            <Card v-if="panel.totals" :pt="cardPt">
                <template #title>Totaal KPI</template>
                <template #content>
                    <p class="text-3xl font-bold">
                        {{ panel.totals.kpi_fmt }}
                    </p>
                    <p class="text-sm text-gray-500">
                        Brutomarge / {{ panel.totals.loonkosten_fmt }}
                    </p>
                </template>
            </Card>
            <Card
                v-for="ent in panel.entities"
                :key="ent.admin_code"
                :pt="cardPt"
            >
                <template #title>{{ ent.label }}</template>
                <template #content>
                    <p class="text-3xl font-bold">{{ ent.kpi_fmt }}</p>
                    <p class="text-sm text-gray-500">
                        {{ ent.bruto_marge_fmt }} / {{ ent.loonkosten_fmt }}
                    </p>
                </template>
            </Card>
        </div>

        <Message
            v-else-if="!embedded"
            severity="info"
            :closable="false"
            class="!mb-4"
        >
            <span class="text-sm">
                Geen bruto marge per loonkosten voor de geselecteerde periode.
            </span>
        </Message>

        <template v-if="isLive && entitiesWithMonths.length">
            <div
                :class="
                    embedded
                        ? 'mt-4 h-52 min-h-[12rem]'
                        : 'mb-6 rounded-lg border border-gray-100 bg-white p-4'
                "
            >
                <h3
                    v-if="!embedded"
                    class="mb-3 text-sm font-semibold text-gray-800"
                >
                    KPI maandtrend per entiteit
                </h3>
                <div :class="embedded ? 'h-full' : 'h-56 min-h-[14rem]'">
                    <Chart
                        type="line"
                        :data="kpiTrendChart"
                        :options="kpiTrendOptions"
                        class="h-full w-full"
                    />
                </div>
            </div>

            <template v-if="!embedded">
            <div
                v-for="ent in entitiesWithMonths"
                :key="'mpl-chart-' + ent.admin_code"
                class="mb-6 rounded-lg border border-gray-100 bg-white p-4"
            >
                <h3 class="mb-3 text-sm font-semibold text-gray-800">
                    {{ ent.label }} — maandtrend
                </h3>
                <div class="mb-4 h-48 min-h-[12rem]">
                    <Chart
                        type="line"
                        :data="entityMargeChart(ent)"
                        :options="margeChartOptions"
                        class="h-full w-full"
                    />
                </div>
                <DataTable
                    :value="sortedMonths(ent.months)"
                    striped-rows
                    show-gridlines
                    class="p-datatable-sm text-sm"
                    :empty-message="'Geen maanden.'"
                >
                    <template #header>
                        <span class="font-semibold">
                            Maandoverzicht (alleen definitieve maanden in
                            jaartotalen)
                        </span>
                    </template>
                    <Column header="Maand">
                        <template #body="{ data }">
                            {{ monthLabel(data) }}
                        </template>
                    </Column>
                    <Column
                        field="bruto_marge_fmt"
                        header="Brutomarge"
                    />
                    <Column field="loonkosten_fmt" header="Loonkosten" />
                    <Column field="kpi_fmt" header="KPI" />
                    <Column header="Status">
                        <template #body="{ data }">
                            <Tag
                                :severity="
                                    data.definitief ? 'success' : 'warn'
                                "
                                :value="
                                    data.definitief
                                        ? 'Definitief'
                                        : 'Voorlopig'
                                "
                            />
                        </template>
                    </Column>
                </DataTable>
            </div>
            </template>
        </template>

        <div
            v-else-if="embedded"
            class="mt-4 rounded-md border border-dashed border-gray-200 bg-gray-50/80 px-4 py-6 text-center"
        >
            <p class="text-sm font-medium text-gray-500">
                Geen maandtrend beschikbaar
            </p>
            <p class="mt-1 text-xs text-gray-500">
                Bruto marge per loonkosten — Cashweb
            </p>
        </div>

        <div
            v-if="showPartialBlock && !embedded"
            class="mt-6 rounded-lg border border-gray-100 bg-gray-50/60 p-4"
        >
            <h3 class="mb-3 text-sm font-semibold text-gray-800">
                Gedeeltelijke loonrekeningen (4130 / 4512)
            </h3>
            <p class="mb-3 text-xs text-gray-500">
                AFC & ACC — pensioenlasten en reis/verblijf
            </p>
            <div class="grid gap-4 sm:grid-cols-2">
                <Card
                    v-for="ent in panel.entities.filter((e) =>
                        ['pgl1', 'acco'].includes(e.admin_code),
                    )"
                    :key="'pw-' + ent.admin_code"
                    :pt="cardPt"
                >
                    <template #title>{{ ent.label }}</template>
                    <template #content>
                        <ul class="space-y-1 text-sm text-gray-700">
                            <li
                                v-for="acct in panel.partialAccounts"
                                :key="acct"
                            >
                                Rekening {{ acct }}:
                                <strong>{{
                                    ent.partial_wage?.[acct] != null
                                        ? `€ ${Number(ent.partial_wage[acct]).toLocaleString('nl-NL')}`
                                        : '—'
                                }}</strong>
                            </li>
                        </ul>
                    </template>
                </Card>
            </div>
        </div>
    </div>
</template>
