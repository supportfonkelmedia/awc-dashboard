<script setup>
import FinanceKpiDrawer from '@/Components/Management/FinanceKpiDrawer.vue';
import KpiExplainDrawer from '@/Components/Management/KpiExplainDrawer.vue';
import MtKpiCard from '@/Components/Management/MtKpiCard.vue';
import MtSectionCard from '@/Components/Management/MtSectionCard.vue';
import RevenuePerLobPanel from '@/Components/Management/RevenuePerLobPanel.vue';
import MetricSparkCard from '@/Components/Management/MetricSparkCard.vue';
import { useMtKpiData } from '@/composables/useMtKpiData';
import { useMtWmsLoader } from '@/composables/useMtWmsLoader';
import ManagementLayout from '@/Layouts/ManagementLayout.vue';
import { Deferred, Head, Link, router } from '@inertiajs/vue3';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Chart from 'primevue/chart';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Dropdown from 'primevue/dropdown';
import Message from 'primevue/message';
import TabPanel from 'primevue/tabpanel';
import TabView from 'primevue/tabview';
import Tag from 'primevue/tag';
import { computed, ref, watch } from 'vue';

const props = defineProps({
    peliqan: { type: Object, default: null },
    peliqanError: { type: String, default: null },
    filters: {
        type: Object,
        required: true,
    },
});

const brandBlue = '#1e3a5f';

const form = ref({
    book_year: props.filters.book_year,
    month: props.filters.month,
    start_date: props.filters.start_date,
    end_date: props.filters.end_date,
});

watch(
    () => props.filters,
    (f) => {
        form.value = {
            book_year: f.book_year,
            month: f.month,
            start_date: f.start_date,
            end_date: f.end_date,
        };
    },
    { deep: true },
);

const currentYear = new Date().getFullYear();
const bookYearOptions = [currentYear, currentYear - 1, currentYear - 2].map(
    (y) => ({ label: String(y), value: String(y) }),
);

const monthOptions = [
    { label: 'Heel jaar (YTD huidig boekjaar)', value: 'all' },
    { label: 'Januari', value: '1' },
    { label: 'Februari', value: '2' },
    { label: 'Maart', value: '3' },
    { label: 'April', value: '4' },
    { label: 'Mei', value: '5' },
    { label: 'Juni', value: '6' },
    { label: 'Juli', value: '7' },
    { label: 'Augustus', value: '8' },
    { label: 'September', value: '9' },
    { label: 'Oktober', value: '10' },
    { label: 'November', value: '11' },
    { label: 'December', value: '12' },
];

function applyFilters() {
    router.get(
        route('mt.dashboard'),
        {
            book_year: form.value.book_year,
            month: form.value.month,
            start_date: form.value.start_date,
            end_date: form.value.end_date,
        },
        { preserveState: true, preserveScroll: true, replace: true },
    );
}

const dataError = computed(() => props.peliqan?.error ?? null);

const cw = computed(() => props.peliqan?.data?.cashweb ?? null);
const hs = computed(() => props.peliqan?.data?.hubspot ?? null);
const sp = computed(() => props.peliqan?.data?.sprinter ?? null);

const applied = computed(() => props.peliqan?.filters ?? null);

const peliqanRef = computed(() => props.peliqan);
const appliedRef = computed(() => applied.value);

const { wmsPeliqan, wmsLoading, wmsError } = useMtWmsLoader();

const {
    strategicCards,
    journeySections,
    tacticalCards,
    entitySections,
    financeDetail,
    financeDrawerRows,
    financePeriodLabel,
    revenuePerLobPanel,
} = useMtKpiData(peliqanRef, appliedRef, wmsPeliqan, wmsLoading);

const financeDrawerOpen = ref(false);
const selectedFinanceKpi = ref(null);

const kpiDrawerOpen = ref(false);
const selectedKpi = ref(null);

function openKpiDrawer(card) {
    selectedKpi.value = card;
    kpiDrawerOpen.value = true;
}

const financeDrawerTableRows = computed(() => {
    const id = selectedFinanceKpi.value?.id;
    if (!id) return [];
    return financeDrawerRows.value[id] ?? [];
});

function openFinanceDrawer(card) {
    selectedFinanceKpi.value = card;
    financeDrawerOpen.value = true;
}

function fmtEur(n) {
    if (n == null || Number.isNaN(Number(n))) return '—';
    const v = Number(n);
    if (Math.abs(v) >= 1_000_000) return `€${(v / 1_000_000).toFixed(2)}M`;
    if (Math.abs(v) >= 1_000)
        return `€${(v / 1_000).toFixed(1)}K`.replace('.', ',');
    return `€${Math.round(v).toLocaleString('nl-NL')}`;
}

function deltaTxt(cur, prev) {
    if (prev == null || Number(prev) === 0) return '';
    const p =
        ((Number(cur) - Number(prev)) / Math.abs(Number(prev))) * 100;
    const s = `${p >= 0 ? '+' : ''}${p.toFixed(1)}%`;
    return s;
}

function deltaPositive(cur, prev) {
    if (prev == null || Number(prev) === 0) return true;
    return Number(cur) >= Number(prev);
}

function buildSpark(rows) {
    const byP = {};
    for (const row of rows || []) {
        const p = Number(row.periode);
        if (Number.isNaN(p)) continue;
        byP[p] = (byP[p] || 0) + Number(row.omzet ?? 0);
    }
    const keys = Object.keys(byP).sort((a, b) => Number(a) - Number(b));
    if (!keys.length) return [0, 0, 0, 0, 0, 0, 0, 0];
    return keys.map((k) => byP[k]);
}

const omzetSpark = computed(() =>
    buildSpark(cw.value?.omzet_trend_per_maand),
);

const shipRows = computed(() => sp.value?.shipments ?? []);

const tripleLob = computed(() => {
    const rows = cw.value?.triple_lob_customers ?? [];
    const nAll = rows.length;
    let nTriple = 0;
    let omzTriple = 0;
    let omzAll = 0;
    for (const r of rows) {
        const o = Number(r.omzet ?? 0);
        omzAll += o;
        if (Number(r.aantal_lob) >= 3) {
            nTriple += 1;
            omzTriple += o;
        }
    }
    return {
        nAll,
        nTriple,
        pctKlant: nAll ? Math.round((nTriple / nAll) * 1000) / 10 : 0,
        pctOmz: omzAll ? Math.round((omzTriple / omzAll) * 1000) / 10 : 0,
    };
});

const deals = computed(() => hs.value?.deals ?? []);
const dealsYoY = computed(() => hs.value?.deals_yoy_counts?.[0] ?? {});

const dealKpis = computed(() => {
    const d = deals.value;
    const n = d.length;
    const won = d.filter(
        (x) =>
            String(x.is_gesloten) === 'true' && Number(x.amount ?? 0) > 0,
    ).length;
    const wr = n ? Math.round((won / n) * 1000) / 10 : 0;
    const nV = Number(dealsYoY.value?.n ?? 0);
    const wonV = Number(dealsYoY.value?.won ?? 0);
    const wrV = nV ? Math.round((wonV / nV) * 1000) / 10 : 0;
    return { n, won, wr, nV, wonV, wrV };
});

const tickets = computed(() => hs.value?.tickets ?? []);
const ticketsYoY = computed(() =>
    Number(hs.value?.tickets_yoy_count?.[0]?.n ?? 0),
);

const ticketKpis = computed(() => {
    const t = tickets.value;
    const n = t.length;
    let open = 0;
    let ttc = 0;
    let ttcN = 0;
    for (const row of t) {
        if (!row.closed_date) open += 1;
        const m = Number(row.time_to_close);
        if (!Number.isNaN(m) && m > 0) {
            ttc += m;
            ttcN += 1;
        }
    }
    const avgTtc = ttcN ? ttc / ttcN : null;
    return { n, open, closed: n - open, avgTtc };
});

const dealWeekChart = computed(() => {
    const rows = hs.value?.deals_per_week_proxy ?? [];
    const labels = rows.map((r) =>
        String(r.week ?? '').slice(0, 10),
    );
    const data = rows.map((r) => Number(r.deals ?? 0));
    return {
        labels: labels.length ? labels : ['—'],
        datasets: [
            {
                label: 'Nieuwe deals / week',
                data: data.length ? data : [0],
                borderColor: brandBlue,
                backgroundColor: brandBlue,
                tension: 0.35,
                fill: false,
            },
        ],
    };
});

const dealWeekOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: true } },
    scales: {
        x: { ticks: { maxRotation: 45, minRotation: 0 } },
        y: { beginAtZero: true },
    },
};

const salRows = computed(() => cw.value?.salarissen_SAL ?? []);

const loonTotaal = computed(() => {
    let s = 0;
    for (const r of salRows.value) {
        s += Number(r.loon_debet ?? 0);
    }
    return s;
});

const cardPt = {
    root: { class: 'border border-gray-100 shadow-sm' },
    body: { class: '!p-0' },
    caption: { class: 'border-b border-gray-100 px-5 pb-3 pt-5' },
    title: {
        class: 'text-sm font-semibold leading-tight text-gray-900',
    },
    content: { class: '!px-5 !pb-5 !pt-4' },
};

const tabViewPt = {
    panelContainer: {
        class: '!bg-transparent !px-0 !py-4',
    },
    tab: {
        content: {
            class: '!bg-transparent !p-0',
        },
    },
};

const filterClass =
    'flex min-w-[140px] flex-col gap-1 rounded-lg border border-gray-200 bg-white px-3 py-2';
const labelClass =
    'text-[10px] font-semibold uppercase tracking-wider text-gray-500';
</script>

<template>
    <Head title="MT Dashboard" />

    <ManagementLayout>
        <div class="mx-auto max-w-[1600px] px-4 py-6 lg:px-6">
            <div
                class="mb-6 flex flex-col gap-3 border-b border-gray-200 pb-6 lg:flex-row lg:items-end lg:justify-between"
            >
                <div>
                    <h1
                        class="text-2xl font-bold tracking-tight text-gray-900 lg:text-3xl"
                    >
                        MT Dashboard
                    </h1>
                    <p class="mt-1 max-w-2xl text-sm text-gray-600">
                        Amsterdam Companies · AWC · AFC · ACC — financieel
                        (Cashweb), commercieel (HubSpot), AFC (Sprinter3000).
                        Data via Peliqan.
                    </p>
                    <p
                        v-if="applied"
                        class="mt-2 text-xs text-gray-500"
                    >
                        <template v-if="applied.period_label">
                            Cashweb:
                            <span class="font-medium text-gray-700">{{
                                applied.period_label
                            }}</span>
                            <span
                                v-if="applied.book_periods_prior"
                                class="text-gray-400"
                            >
                                (vorig:
                                <span class="font-mono">{{
                                    applied.book_periods_prior
                                }}</span
                                >)
                            </span>
                        </template>
                        <template v-else>
                            Boekjaar
                            <span class="font-medium text-gray-700">{{
                                applied.book_year
                            }}</span>
                            · book_period
                            <span class="font-mono text-gray-700">{{
                                applied.book_periods
                            }}</span>
                        </template>
                        · HubSpot/Sprinter
                        <span class="font-mono text-gray-700">{{
                            applied.start_date
                        }}</span>
                        →
                        <span class="font-mono text-gray-700">{{
                            applied.end_date
                        }}</span>
                        <span
                            v-if="applied.yoy_compare_window"
                            class="block mt-1 text-gray-400"
                        >
                            YoY-venster:
                            <span class="font-mono">{{
                                applied.yoy_compare_window.start
                            }}</span>
                            →
                            <span class="font-mono">{{
                                applied.yoy_compare_window.end
                            }}</span>
                        </span>
                    </p>
                </div>
            </div>

            <Card :pt="cardPt" class="mb-6">
                <template #content>
                    <div
                        class="flex flex-wrap items-end gap-3 lg:gap-4"
                    >
                        <div :class="filterClass">
                            <span :class="labelClass">Boekjaar</span>
                            <Dropdown
                                v-model="form.book_year"
                                :options="bookYearOptions"
                                option-label="label"
                                option-value="value"
                                class="w-full min-w-[7rem]"
                            />
                        </div>
                        <div :class="filterClass">
                            <span :class="labelClass">Cashweb-maand</span>
                            <Dropdown
                                v-model="form.month"
                                :options="monthOptions"
                                option-label="label"
                                option-value="value"
                                class="w-full min-w-[10rem]"
                            />
                        </div>
                        <div :class="filterClass">
                            <span :class="labelClass">Van (HS / Sprinter)</span>
                            <input
                                v-model="form.start_date"
                                type="date"
                                class="w-full rounded border border-gray-200 px-2 py-1.5 text-sm"
                            />
                        </div>
                        <div :class="filterClass">
                            <span :class="labelClass">Tot</span>
                            <input
                                v-model="form.end_date"
                                type="date"
                                class="w-full rounded border border-gray-200 px-2 py-1.5 text-sm"
                            />
                        </div>
                        <Button
                            label="Toepassen"
                            icon="pi pi-refresh"
                            class="shrink-0"
                            @click="applyFilters"
                        />
                    </div>
                </template>
            </Card>

            <Message
                v-if="peliqanError"
                severity="warn"
                class="mb-6"
                :closable="false"
            >
                <span class="text-sm">{{ peliqanError }}</span>
            </Message>

            <Message
                v-if="wmsPeliqan?.meta?.stale"
                severity="warn"
                class="mb-6"
                :closable="false"
            >
                <span class="text-sm">
                    7T WMS toont gecachte data (Peliqan timeout) — waarden
                    kunnen verouderd zijn.
                </span>
            </Message>

            <Message
                v-else-if="wmsError"
                severity="warn"
                class="mb-6"
                :closable="false"
            >
                <span class="text-sm">
                    7T WMS (AWC): {{ wmsError }} — overige MT-data blijft
                    zichtbaar; bezettingsgraad en storage lead time tonen geen
                    live waarde.
                </span>
            </Message>

            <Deferred data="peliqan">
                <template #fallback>
                    <div class="mt-2 space-y-6">
                        <div
                            v-for="s in 3"
                            :key="`mt-skel-${s}`"
                            class="rounded-xl border border-gray-100 bg-white p-5 shadow-sm"
                        >
                            <div
                                class="mb-4 h-5 w-56 animate-pulse rounded bg-gray-200"
                            ></div>
                            <div
                                class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
                            >
                                <div
                                    v-for="n in 4"
                                    :key="`mt-skel-${s}-${n}`"
                                    class="h-28 animate-pulse rounded-lg bg-gray-100"
                                ></div>
                            </div>
                        </div>
                    </div>
                </template>

                <Message
                    v-if="dataError"
                    severity="warn"
                    class="mb-6"
                    :closable="false"
                >
                    <span class="text-sm">{{ dataError }}</span>
                </Message>

                <TabView
                    class="mt-2 [&_.p-tabview-tablist]:flex-wrap"
                    :pt="tabViewPt"
                >
                    <TabPanel header="Samenvatting">
                    <div class="space-y-6">
                        <Message
                            severity="info"
                            :closable="false"
                            class="!mb-0"
                        >
                            <span class="text-sm text-gray-700">
                                KPI-structuur volgens AWC KPI-framework.
                                Alleen status
                                <strong class="font-medium">Live</strong>
                                toont een meetwaarde.
                            </span>
                        </Message>

                        <MtSectionCard
                            title="Strategische KPI's"
                            subtitle="Vijf bedrijfs-KPI's — anker voor operationeel en tactisch"
                        >
                            <div
                                class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
                            >
                                <MtKpiCard
                                    v-for="c in strategicCards"
                                    :key="'strat-' + c.id"
                                    :title="c.title"
                                    :theme="c.theme"
                                    :status="c.status"
                                    :value="c.value"
                                    :delta="c.delta"
                                    :delta-positive="c.deltaPositive"
                                    :footer="c.footer"
                                    :note="c.note"
                                    explainable
                                    @explain="openKpiDrawer(c)"
                                />
                            </div>
                            <div
                                class="mt-6 border-t border-gray-100 pt-6"
                            >
                                <RevenuePerLobPanel
                                    :panel="revenuePerLobPanel"
                                    embedded
                                />
                            </div>
                        </MtSectionCard>

                        <MtSectionCard
                            title="Operationeel — klantreis"
                            subtitle="Gekoppeld aan strategische KPI via context"
                        >
                            <div class="space-y-5">
                                <div
                                    v-for="stage in journeySections"
                                    :key="stage.id"
                                    class="rounded-lg border border-gray-100 bg-gray-50/60 p-4"
                                >
                                    <h3
                                        class="mb-3 text-sm font-semibold text-gray-800"
                                    >
                                        {{ stage.label }}
                                    </h3>
                                    <div
                                        class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
                                    >
                                        <MtKpiCard
                                            v-for="c in stage.cards"
                                            :key="stage.id + '-' + c.id"
                                            :title="c.title"
                                            :status="c.status"
                                            :value="c.value"
                                            :delta="c.delta"
                                            :delta-positive="c.deltaPositive"
                                            :footer="c.footer"
                                            :note="c.note"
                                            :strategic-link="c.strategicLink"
                                            compact
                                            explainable
                                            @explain="openKpiDrawer(c)"
                                        />
                                    </div>
                                </div>
                            </div>
                        </MtSectionCard>

                        <MtSectionCard title="Tactisch / ondersteunend">
                            <div
                                class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
                            >
                                <MtKpiCard
                                    v-for="c in tacticalCards"
                                    :key="'tac-' + c.id"
                                    :title="c.title"
                                    :status="c.status"
                                    :value="c.value"
                                    :footer="c.footer"
                                    :note="c.note"
                                    :strategic-link="c.strategicLink"
                                    compact
                                    explainable
                                    @explain="openKpiDrawer(c)"
                                />
                            </div>
                        </MtSectionCard>

                        <MtSectionCard
                            title="Per entiteit"
                            subtitle="Lokale metingen — drill-down naar entiteit-dashboard"
                        >
                            <div class="space-y-5">
                                <div
                                    v-for="entity in entitySections"
                                    :key="entity.code"
                                    class="rounded-lg border border-gray-100 bg-gray-50/60 p-4"
                                >
                                    <div
                                        class="mb-3 flex flex-wrap items-center justify-between gap-2"
                                    >
                                        <h3
                                            class="text-sm font-semibold text-gray-800"
                                        >
                                            {{ entity.label }}
                                            <span
                                                class="ml-2 text-xs font-normal text-gray-500"
                                                >{{ entity.source }}</span
                                            >
                                        </h3>
                                        <Link
                                            :href="route(entity.routeName)"
                                            class="inline-flex items-center gap-1 text-xs font-semibold text-[#ff7020] hover:underline"
                                        >
                                            Drill-down
                                            <i
                                                class="pi pi-arrow-right text-[10px]"
                                            />
                                        </Link>
                                    </div>
                                    <div
                                        class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                                    >
                                        <MtKpiCard
                                            v-for="c in entity.cards"
                                            :key="entity.code + '-' + c.id"
                                            :title="c.title"
                                            :status="c.status"
                                            :value="c.value"
                                            :delta="c.delta"
                                            :delta-positive="c.deltaPositive"
                                            :footer="c.footer"
                                            :note="c.note"
                                            :strategic-link="c.strategicLink"
                                            compact
                                            explainable
                                            @explain="openKpiDrawer(c)"
                                        />
                                    </div>
                                </div>
                            </div>
                        </MtSectionCard>
                    </div>
                </TabPanel>

                <TabPanel header="Financieel">
                    <div class="space-y-6">
                        <MtSectionCard
                            title="Revenue per Line of Business"
                            subtitle="Strategische KPI — omzet per business line (sub_administration)"
                        >
                            <RevenuePerLobPanel
                                :panel="revenuePerLobPanel"
                                embedded
                            />
                        </MtSectionCard>

                        <MtSectionCard
                            title="Financiële bouwstenen (detail)"
                            subtitle="Niet de strategische kop — klik een tegel voor berekening per admin"
                            :accent="false"
                        >
                            <div
                                class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
                            >
                                <MetricSparkCard
                                    v-for="c in financeDetail"
                                    :key="c.id"
                                    :title="c.title"
                                    :value="c.value"
                                    :delta="c.delta"
                                    :delta-positive="c.deltaPositive"
                                    :footer="c.footer"
                                    :spark-data="omzetSpark"
                                    clickable
                                    @click="openFinanceDrawer(c)"
                                />
                            </div>
                            <FinanceKpiDrawer
                                v-model:visible="financeDrawerOpen"
                                :kpi="selectedFinanceKpi"
                                :rows="financeDrawerTableRows"
                                :period-label="financePeriodLabel"
                            />
                        </MtSectionCard>

                        <MtSectionCard
                            title="Triple LOB"
                            subtitle="Klanten met omzet in ≥3 business lines"
                            :accent="false"
                        >
                            <p class="text-2xl font-bold text-gray-900">
                                {{ tripleLob.nTriple }} / {{ tripleLob.nAll }}
                                <span
                                    class="text-base font-normal text-gray-500"
                                    >klanten (≥3 LOB)</span
                                >
                            </p>
                            <p class="mt-2 text-sm text-gray-600">
                                % klanten:
                                <strong>{{ tripleLob.pctKlant }}%</strong> ·
                                % omzet:
                                <strong>{{ tripleLob.pctOmz }}%</strong>
                            </p>
                        </MtSectionCard>
                    </div>
                </TabPanel>

                <TabPanel header="Commercieel">
                    <div class="space-y-6">
                        <MtSectionCard
                            title="Pipeline KPI's"
                            subtitle="HubSpot deals in geselecteerde periode"
                        >
                            <div class="grid gap-4 sm:grid-cols-3">
                                <Card :pt="cardPt">
                                    <template #title>Nieuwe deals</template>
                                    <template #content>
                                        <p class="text-3xl font-bold">
                                            {{ dealKpis.n }}
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            YoY zelfde venster:
                                            {{ dealKpis.nV }}
                                            <span
                                                v-if="dealKpis.nV"
                                                class="font-medium text-gray-700"
                                                >({{
                                                    deltaTxt(
                                                        dealKpis.n,
                                                        dealKpis.nV,
                                                    )
                                                }})</span
                                            >
                                        </p>
                                    </template>
                                </Card>
                                <Card :pt="cardPt">
                                    <template #title>Gewonnen deals</template>
                                    <template #content>
                                        <p class="text-3xl font-bold">
                                            {{ dealKpis.won }}
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Proxy: gesloten + amount &gt; 0
                                        </p>
                                    </template>
                                </Card>
                                <Card :pt="cardPt">
                                    <template #title>Win rate</template>
                                    <template #content>
                                        <p class="text-3xl font-bold">
                                            {{ dealKpis.wr }}%
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Vorig: {{ dealKpis.wrV }}%
                                            <span
                                                v-if="dealKpis.wrV"
                                                class="font-medium"
                                                >({{
                                                    deltaTxt(
                                                        dealKpis.wr,
                                                        dealKpis.wrV,
                                                    )
                                                }})</span
                                            >
                                        </p>
                                    </template>
                                </Card>
                            </div>
                        </MtSectionCard>

                        <MtSectionCard
                            title="Deals per week"
                            subtitle="Proxy voor ICP-interacties"
                        >
                            <div class="h-56">
                                <Chart
                                    type="line"
                                    :data="dealWeekChart"
                                    :options="dealWeekOpts"
                                    class="h-full"
                                />
                            </div>
                        </MtSectionCard>

                        <MtSectionCard title="Deals (selectie)">
                            <DataTable
                                :value="deals.slice(0, 100)"
                                striped-rows
                                show-gridlines
                                scrollable
                                scroll-height="320px"
                                class="p-datatable-sm text-sm"
                                :empty-message="'Geen deals in periode.'"
                            >
                                <Column field="dealname" header="Deal" />
                                <Column field="stage_label" header="Stage" />
                                <Column field="amount" header="Amount" />
                                <Column field="createdat" header="Aangemaakt" />
                            </DataTable>
                        </MtSectionCard>

                        <MtSectionCard
                            title="Churn & onboarding"
                            subtitle="Proxies — definities nog af te stemmen"
                            :accent="false"
                        >
                            <div class="grid gap-4 lg:grid-cols-2">
                                <Card :pt="cardPt">
                                    <template #title>
                                        Churn proxy (lost / €0)
                                    </template>
                                    <template #content>
                                        <p class="text-xl font-semibold">
                                            {{
                                                (hs?.churn_deals_proxy ?? [])
                                                    .length
                                            }}
                                            deals
                                        </p>
                                        <DataTable
                                            :value="
                                                (
                                                    hs?.churn_deals_proxy ?? []
                                                ).slice(0, 15)
                                            "
                                            class="mt-3 p-datatable-sm text-sm"
                                            :empty-message="'Geen.'"
                                        >
                                            <Column
                                                field="dealname"
                                                header="Deal"
                                            />
                                            <Column
                                                field="stage_label"
                                                header="Stage"
                                            />
                                        </DataTable>
                                    </template>
                                </Card>
                                <Card :pt="cardPt">
                                    <template #title>
                                        Onboarding proxy (time-to-close)
                                    </template>
                                    <template #content>
                                        <DataTable
                                            :value="
                                                (
                                                    hs?.onboarding_proxy ?? []
                                                ).slice(0, 20)
                                            "
                                            class="p-datatable-sm text-sm"
                                            :empty-message="'Geen gesloten wins in periode.'"
                                        >
                                            <Column
                                                field="dealname"
                                                header="Deal"
                                            />
                                            <Column
                                                field="createdat"
                                                header="Created"
                                            />
                                            <Column
                                                field="closedate"
                                                header="Closed"
                                            />
                                        </DataTable>
                                    </template>
                                </Card>
                            </div>
                        </MtSectionCard>
                    </div>
                </TabPanel>

                <TabPanel header="AFC — Sprinter">
                    <div class="space-y-6">
                        <MtSectionCard
                            title="Zendingen"
                            subtitle="Sprinter3000 · report_date in filter"
                        >
                            <div class="mb-4 flex flex-wrap gap-2">
                                <Tag severity="success" value="sprinter3000" />
                                <Tag
                                    :value="`${shipRows.length} zendingen in filter`"
                                />
                            </div>
                            <DataTable
                                :value="shipRows.slice(0, 150)"
                                striped-rows
                                show-gridlines
                                scrollable
                                scroll-height="480px"
                                class="p-datatable-sm text-sm"
                                :empty-message="'Geen zendingen voor gekozen datums.'"
                            >
                                <Column field="shipment_number" header="#" />
                                <Column
                                    field="report_date"
                                    header="Reportdatum"
                                />
                                <Column field="shipment_mode" header="Mode" />
                                <Column
                                    field="shipment_status_code"
                                    header="Status"
                                />
                                <Column field="klant_naam" header="Klant" />
                                <Column
                                    field="total_sales_amount"
                                    header="Omzet"
                                />
                                <Column field="total_gpm_amount" header="GPM" />
                            </DataTable>
                        </MtSectionCard>

                        <MtSectionCard
                            title="Modal split"
                            subtitle="Aantal zendingen en gem. GPM per mode"
                        >
                            <DataTable
                                :value="sp?.shipment_modes ?? []"
                                striped-rows
                                show-gridlines
                                class="p-datatable-sm text-sm"
                                :empty-message="'—'"
                            >
                                <Column field="shipment_mode" header="Mode" />
                                <Column field="n" header="Aantal" />
                                <Column field="gem_gpm" header="Gem. GPM" />
                            </DataTable>
                        </MtSectionCard>
                    </div>
                </TabPanel>

                <TabPanel header="Mensen & HR">
                    <div class="space-y-6">
                        <Message severity="info" :closable="false" class="!mb-0">
                            <span class="text-sm text-gray-700">
                                FTE-proxy via Cashweb SAL-dagboek (Hooray nog
                                niet gekoppeld).
                            </span>
                        </Message>

                        <MtSectionCard
                            title="Loonkosten (SAL-proxy)"
                            subtitle="Cashweb dagboek SAL — debet som"
                        >
                            <Card :pt="cardPt" class="mb-4">
                                <template #title
                                    >Loonkosten SAL (debet som)</template
                                >
                                <template #content>
                                    <p class="text-3xl font-bold text-gray-900">
                                        {{ fmtEur(loonTotaal) }}
                                    </p>
                                    <p class="text-sm text-gray-500">
                                        Detail per admin/periode hieronder.
                                    </p>
                                </template>
                            </Card>
                            <DataTable
                                :value="salRows"
                                striped-rows
                                show-gridlines
                                scrollable
                                scroll-height="400px"
                                class="p-datatable-sm text-sm"
                                :empty-message="'Geen SAL-mutaties voor filter.'"
                            >
                                <Column field="admin_code" header="Admin" />
                                <Column field="book_period" header="Periode" />
                                <Column field="loon_debet" header="Loon debet" />
                                <Column
                                    field="loon_credit"
                                    header="Loon credit"
                                />
                                <Column
                                    field="unieke_relaties"
                                    header="Relaties"
                                />
                            </DataTable>
                        </MtSectionCard>

                        <MtSectionCard
                            title="A/B players · eNPS · Intern/extern"
                            subtitle="Hooray / Microsoft Forms — nog niet gemeten"
                            :accent="false"
                        >
                            <p class="text-sm text-gray-600">
                                Handmatige invoer / Hooray / Forms — volgens
                                MT-bron nog placeholders. Toon hier later echte
                                velden zodra gekoppeld.
                            </p>
                        </MtSectionCard>
                    </div>
                </TabPanel>

                <TabPanel header="Tickets & NPS">
                    <div class="space-y-6">
                        <MtSectionCard
                            title="Ticket KPI's"
                            subtitle="HubSpot Service Hub"
                        >
                            <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                                <Card :pt="cardPt">
                                    <template #title>Tickets</template>
                                    <template #content>
                                        <p class="text-3xl font-bold">
                                            {{ ticketKpis.n }}
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            YoY: {{ ticketsYoY }}
                                        </p>
                                    </template>
                                </Card>
                                <Card :pt="cardPt">
                                    <template #title>Open</template>
                                    <template #content>
                                        <p class="text-3xl font-bold">
                                            {{ ticketKpis.open }}
                                        </p>
                                    </template>
                                </Card>
                                <Card :pt="cardPt">
                                    <template #title>Gesloten</template>
                                    <template #content>
                                        <p class="text-3xl font-bold">
                                            {{ ticketKpis.closed }}
                                        </p>
                                    </template>
                                </Card>
                                <Card :pt="cardPt">
                                    <template #title>Gem. TTC</template>
                                    <template #content>
                                        <p class="text-2xl font-bold">
                                            {{
                                                ticketKpis.avgTtc != null
                                                    ? ticketKpis.avgTtc > 60
                                                        ? `${(ticketKpis.avgTtc / 60).toFixed(1)} u`
                                                        : `${Math.round(ticketKpis.avgTtc)} min`
                                                    : '—'
                                            }}
                                        </p>
                                    </template>
                                </Card>
                            </div>
                        </MtSectionCard>

                        <MtSectionCard title="Tickets (selectie)">
                            <DataTable
                                :value="tickets.slice(0, 120)"
                                striped-rows
                                show-gridlines
                                scrollable
                                scroll-height="400px"
                                class="p-datatable-sm text-sm"
                                :empty-message="'Geen tickets.'"
                            >
                                <Column field="subject" header="Onderwerp" />
                                <Column field="status_label" header="Status" />
                                <Column
                                    field="hs_ticket_priority"
                                    header="Prioriteit"
                                />
                                <Column field="createdat" header="Aangemaakt" />
                                <Column field="time_to_close" header="TTC" />
                            </DataTable>
                        </MtSectionCard>

                        <MtSectionCard
                            title="Feedback / NPS (sample)"
                            subtitle="NPS/eNPS nog niet gemeten — HubSpot sample data"
                            :accent="false"
                        >
                            <DataTable
                                :value="hs?.feedback_submissions_sample ?? []"
                                striped-rows
                                show-gridlines
                                class="p-datatable-sm text-sm"
                                :empty-message="'Geen feedback records.'"
                            >
                                <Column field="id" header="ID" />
                                <Column field="createdat" header="Created" />
                                <Column field="archived" header="Archived" />
                            </DataTable>
                        </MtSectionCard>
                    </div>
                    </TabPanel>
                </TabView>
            </Deferred>

            <KpiExplainDrawer
                v-model:visible="kpiDrawerOpen"
                :kpi="selectedKpi"
            />
        </div>
    </ManagementLayout>
</template>
