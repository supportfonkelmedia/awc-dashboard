<script setup>
import KpiAfcSprinterAlert from '@/Components/Kpi/KpiAfcSprinterAlert.vue';
import KpiCustomerJourneyBar from '@/Components/Kpi/KpiCustomerJourneyBar.vue';
import KpiPijlerSection from '@/Components/Kpi/KpiPijlerSection.vue';
import KpiDrillDownDrawer from '@/Components/Kpi/KpiDrillDownDrawer.vue';
import KpiFeedbackModal from '@/Components/Kpi/KpiFeedbackModal.vue';
import KpiGoalModal from '@/Components/Kpi/KpiGoalModal.vue';
import KpiManualEntryModal from '@/Components/Kpi/KpiManualEntryModal.vue';
import KpiOmzetbrugBanner from '@/Components/Kpi/KpiOmzetbrugBanner.vue';
import KpiScreenHeader from '@/Components/Kpi/KpiScreenHeader.vue';
import KpiStrategischPeriodBar from '@/Components/Kpi/KpiStrategischPeriodBar.vue';
import KpiScreenNav from '@/Components/Kpi/KpiScreenNav.vue';
import KpiSectionBlock from '@/Components/Kpi/KpiSectionBlock.vue';
import KpiTile from '@/Components/Kpi/KpiTile.vue';
import { fetchKpiDrill } from '@/composables/useKpiDrillFetch';
import { useKpiScreenModel } from '@/composables/useKpiScreenModel';
import { useKpiScreenLoader } from '@/composables/useKpiScreenLoader';
import { ENTITEIT_SCOPES, paramFromScope, scopeFromParam } from '@/constants/kpiEntiteiten';
import { KPI_SCREEN_META } from '@/constants/kpiScreens';
import KpiStandaloneLayout from '@/Layouts/KpiStandaloneLayout.vue';
import { Head } from '@inertiajs/vue3';
import Message from 'primevue/message';
import ProgressSpinner from 'primevue/progressspinner';
import { computed, ref, toRef, watch } from 'vue';

const props = defineProps({
    scherm: {
        type: String,
        required: true,
    },
    peliqanError: { type: String, default: null },
    kpiUsesFixture: { type: Boolean, default: false },
});

const meta = computed(() => KPI_SCREEN_META[props.scherm] ?? KPI_SCREEN_META.strategisch);

const { loading, error, payload, reload } = useKpiScreenLoader(toRef(props, 'scherm'));

/** PERIODE (grafieken): 'all' of jaartal; standaard huidig jaar zoals in de mockup. */
const PERIODE_STORAGE_KEY = 'kpi.periode';
const periode = ref(
    (typeof window !== 'undefined' && window.localStorage?.getItem(PERIODE_STORAGE_KEY)) ||
        String(new Date().getFullYear()),
);
watch(periode, (v) => {
    window.localStorage?.setItem(PERIODE_STORAGE_KEY, v);
});

// Alleen strategisch heeft de PERIODE-balk (mockups); andere schermen tonen altijd alles.
const effectivePeriode = computed(() =>
    props.scherm === 'strategisch' ? periode.value : 'all',
);

/**
 * ENTITEIT (alleen strategisch): staat in de URL (?entiteit=awc), zodat een gefilterde
 * weergave te delen is. Standaard het concern.
 */
const entiteit = ref(
    typeof window !== 'undefined'
        ? scopeFromParam(new URLSearchParams(window.location.search).get('entiteit'))
        : 'concern',
);
const effectiveEntiteit = computed(() =>
    props.scherm === 'strategisch' ? entiteit.value : 'concern',
);

// Trendlijnen van AWC/AFC/ACC zitten niet in de schermbundel; één keer ophalen via de drill-route.
const entiteitTrends = ref([]);
const entiteitTrendsError = ref(null);
let entiteitTrendsGeladen = false;

async function loadEntiteitTrends() {
    if (entiteitTrendsGeladen) {
        return;
    }
    entiteitTrendsGeladen = true;
    const { tables, error: err } = await fetchKpiDrill(['kpi_trend']);
    if (err) {
        entiteitTrendsGeladen = false;
        entiteitTrendsError.value = `Trendlijnen per entiteit laden mislukt: ${err}`;

        return;
    }
    entiteitTrendsError.value = null;
    entiteitTrends.value = (tables.kpi_trend ?? []).filter((r) =>
        ENTITEIT_SCOPES.has(String(r.scope_code ?? '')),
    );
}

watch(
    effectiveEntiteit,
    (scope) => {
        if (typeof window !== 'undefined' && props.scherm === 'strategisch') {
            const url = new URL(window.location.href);
            if (scope === 'concern') {
                url.searchParams.delete('entiteit');
            } else {
                url.searchParams.set('entiteit', paramFromScope(scope));
            }
            window.history.replaceState(window.history.state, '', url);
        }
        if (scope !== 'concern') {
            loadEntiteitTrends();
        }
    },
    { immediate: true },
);

const { layoutRowGroups, sections, gepland2027, bijgewerktLabel, periodeOptions } =
    useKpiScreenModel(payload, effectivePeriode, effectiveEntiteit, entiteitTrends);

// Gekozen jaar zonder trendpunten op dit scherm → terug naar Alles.
watch(periodeOptions, (years) => {
    if (periode.value !== 'all' && years.length && !years.includes(periode.value)) {
        periode.value = 'all';
    }
});

const loadError = computed(
    () => props.peliqanError ?? error.value ?? entiteitTrendsError.value,
);

const drillOpen = ref(false);
const drillTile = ref(null);

const invoerOpen = ref(false);
const invoerKpiCode = ref('enps');

const doelOpen = ref(false);
const doelTile = ref(null);

const feedbackOpen = ref(false);
const feedbackTile = ref(null);

function openFeedback(tile = null) {
    feedbackTile.value = tile;
    feedbackOpen.value = true;
}

function openDetails(tile) {
    drillTile.value = tile;
    drillOpen.value = true;
}

const HANDMATIG_KPI = new Set(['enps', 'ab_players', 'ebitda']);

function onInvoer(tile) {
    const code = tile?.kpiCode;
    invoerKpiCode.value =
        code && HANDMATIG_KPI.has(code) ? code : 'enps';
    invoerOpen.value = true;
}

function onSectionInvoer() {
    invoerKpiCode.value = 'enps';
    invoerOpen.value = true;
}

function onDoel(tile) {
    doelTile.value = tile;
    doelOpen.value = true;
}

function isOmzetbrugBanner(banner) {
    return banner.kpiCode === 'omzet_brug' || banner.titel?.toLowerCase().includes('omzetbrug');
}
</script>

<template>
    <Head :title="`KPI — ${meta.title}`" />

    <KpiStandaloneLayout>
        <div class="min-h-full bg-[#f4f4f4]">
            <KpiScreenHeader
                :scherm="scherm"
                :bijgewerkt-label="bijgewerktLabel"
                :controles="payload?.controles_summary ?? { fout: 0, let_op: 0, ok: 0 }"
                :stale="Boolean(payload?.meta?.stale)"
                :fixture="kpiUsesFixture || Boolean(payload?.meta?.fixture)"
                @feedback="openFeedback()"
            />
            <KpiScreenNav :scherm="scherm" />

            <div class="mx-auto max-w-[1440px] px-4 py-6 lg:px-8">
                <KpiStrategischPeriodBar
                    v-if="scherm === 'strategisch'"
                    v-model="periode"
                    v-model:entiteit="entiteit"
                    :years="periodeOptions"
                    class="mb-6"
                />

                <p class="text-[11px] font-semibold uppercase tracking-wider text-[#ff7020]">
                    {{ meta.eyebrow }}
                </p>
                <h1 class="mt-0.5 text-xl font-bold text-gray-900">
                    {{ meta.title }}
                </h1>
                <p v-if="meta.subtitle" class="mt-1 max-w-3xl text-xs text-sky-700">
                    {{ meta.subtitle }}
                </p>

                <KpiCustomerJourneyBar v-if="scherm === 'operationeel'" />

                <KpiAfcSprinterAlert v-if="scherm === 'afc'" :payload="payload" />

                <Message v-if="loadError" severity="warn" class="mt-6 w-full">
                    {{ loadError }}
                </Message>

                <div
                    v-if="loading && !payload"
                    class="mt-8 flex justify-center py-16"
                >
                    <ProgressSpinner style="width: 2.5rem; height: 2.5rem" />
                </div>

                <template v-else-if="payload">
                    <div
                        class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3"
                    >
                        <template
                            v-for="(group, gi) in layoutRowGroups"
                            :key="group.sectionKey"
                        >
                            <KpiPijlerSection
                                v-if="gi > 0"
                                :title="group.sectionHeading"
                            />
                            <template v-for="row in group.items" :key="row.key">
                                <KpiOmzetbrugBanner
                                    v-if="
                                        row.element === 'banner' &&
                                        isOmzetbrugBanner(row)
                                    "
                                    :tile="row"
                                    :prefetched-rows="payload?.kpi_omzetbrug"
                                    @details="openDetails"
                                    @feedback="openFeedback"
                                />
                                <KpiTile
                                    v-else
                                    :tile="row"
                                    @details="openDetails"
                                    @invoer="onInvoer"
                                    @doel="onDoel"
                                    @feedback="openFeedback"
                                />
                            </template>
                        </template>
                    </div>

                    <div v-if="sections.length" class="mt-8 space-y-6">
                        <KpiSectionBlock
                            v-for="sec in sections"
                            :key="sec.key"
                            :section="sec"
                            :payload="payload"
                            :gepland2027="gepland2027"
                            @open-invoer="onSectionInvoer"
                        />
                    </div>

                    <ul
                        v-if="payload.errors?.length"
                        class="mt-6 list-disc pl-5 text-sm text-amber-800"
                    >
                        <li v-for="(err, i) in payload.errors" :key="i">
                            {{ err.table ?? err.view }}:
                            {{ err.error ?? err.warning }}
                        </li>
                    </ul>
                </template>
            </div>
        </div>

        <KpiDrillDownDrawer
            v-model:visible="drillOpen"
            :tile="drillTile"
        />

        <KpiManualEntryModal
            v-model:visible="invoerOpen"
            :kpi-code="invoerKpiCode"
            @saved="reload"
        />

        <KpiFeedbackModal
            v-model:visible="feedbackOpen"
            :scherm="scherm"
            :entiteit="effectiveEntiteit"
            :tile="feedbackTile"
        />

        <KpiGoalModal
            v-model:visible="doelOpen"
            :tile="doelTile"
            @saved="reload"
        />
    </KpiStandaloneLayout>
</template>
