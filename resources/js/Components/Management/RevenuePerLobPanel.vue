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
    showTitle: { type: Boolean, default: true },
});

const lobColors = {
    AWC: '#0ea5e9',
    AFC: '#ff7020',
    ACC: '#6366f1',
};

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

function barColor(lob) {
    const key = String(lob ?? '').toUpperCase();
    return lobColors[key] ?? '#1e3a5f';
}

const chartData = computed(() => {
    const rows = props.panel.rows ?? [];
    return {
        labels: rows.map((r) => r.lob),
        datasets: [
            {
                label: 'Omzet',
                data: rows.map((r) => r.omzet),
                backgroundColor: rows.map((r) => barColor(r.lob)),
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

            <template v-if="isLive && panel.rows?.length">
                <div
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

                <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
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
                    Geen LOB-uitsplitsing beschikbaar
                </p>
                <p v-if="panel.note" class="mt-1 text-xs text-gray-500">
                    {{ panel.note }}
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
                <h4 class="text-sm font-semibold text-gray-800">
                    Revenue per Line of Business
                </h4>
                <p class="mt-0.5 text-xs text-gray-500">
                    {{ panel.lobField }}
                </p>
            </div>
            <Tag
                :value="statusLabel"
                :severity="statusSeverity"
                class="shrink-0 !text-[10px]"
            />
        </div>

        <template v-if="isLive && panel.rows?.length">
            <div
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

            <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
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
                Geen LOB-uitsplitsing beschikbaar
            </p>
            <p v-if="panel.note" class="mt-1 text-xs text-gray-500">
                {{ panel.note }}
            </p>
        </div>
    </div>
</template>
