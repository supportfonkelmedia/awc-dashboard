<script setup>
import { leesbaar } from '@/utils/leesbaar';
import KpiTegelGrafiek from '@/Components/Kpi/KpiTegelGrafiek.vue';
import KpiDrillTabel from '@/Components/Kpi/KpiDrillTabel.vue';
import { Link } from '@inertiajs/vue3';
import Drawer from 'primevue/drawer';
import ProgressSpinner from 'primevue/progressspinner';
import { computed, ref, watch } from 'vue';
import { formatBronBijgewerkt } from '@/utils/kpiFreshness';

const props = defineProps({
    visible: { type: Boolean, default: false },
    tile: { type: Object, default: null },
});

const emit = defineEmits(['update:visible']);

const loading = ref(false);
const error = ref(null);
/** @type {import('vue').Ref<Record<string, Array<object>>>} */
const tables = ref({});
/** @type {import('vue').Ref<Record<string, object>>} */
const tableMeta = ref({});

/** AFC-tegels verwijzen door naar de AFC-analyse (klanten, eigenaren, modaliteit). */
const toonAfcAnalyse = computed(
    () => props.tile?.configRow?.scherm === 'afc' || props.tile?.scopeCode === 'pgl1',
);

const metaRows = computed(() => {
    const o = props.tile?.oordeelRow;
    if (!o) {
        return [];
    }

    const rows = [
        ['Eigenaar', o.eigenaar],
        ['Validator', o.validator],
        ['Bron', o.bron],
        ['Historie-view', o.historie_view],
        ['Update', o.updatefrequentie],
        [
            'Bron bijgewerkt',
            o.bron_bijgewerkt
                ? formatBronBijgewerkt(String(o.bron_bijgewerkt))
                : null,
        ],
    ];

    return rows.filter(([, v]) => v != null && v !== '');
});

watch(
    () => [props.visible, props.tile],
    async ([open, tile]) => {
        if (!open || !tile?.drillViews?.length) {
            return;
        }

        loading.value = true;
        error.value = null;
        tables.value = {};
        tableMeta.value = {};

        try {
            const params = new URLSearchParams({
                bundle: 'drill',
                views: tile.drillViews.join(','),
            });
            // Alleen de rijen van de entiteit of pijplijn van deze tegel (handler v10).
            if (tile.scopeCode) {
                params.set('scope', String(tile.scopeCode));
            }
            const res = await fetch(`${route('kpi.peliqan')}?${params}`, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin',
            });
            const json = await res.json();
            if (!res.ok) {
                error.value =
                    typeof json.error === 'string'
                        ? json.error
                        : 'Drill-down laden mislukt';

                return;
            }
            tables.value = json.tables ?? {};
            tableMeta.value = json.table_meta ?? {};
        } catch (e) {
            error.value = e?.message ?? 'Drill-down laden mislukt';
        } finally {
            loading.value = false;
        }
    },
);

function close() {
    emit('update:visible', false);
}
</script>

<template>
    <Drawer
        :visible="visible"
        position="right"
        class="!w-full sm:!w-[min(36rem,95vw)]"
        @update:visible="emit('update:visible', $event)"
    >
        <template #header>
            <div>
                <p
                    v-if="tile?.pijler"
                    class="text-xs text-gray-500"
                >
                    {{ leesbaar(tile.pijler) }}
                </p>
                <h2 class="text-lg font-semibold text-gray-900">
                    {{ tile?.titel }}
                </h2>
                <p v-if="tile?.eigenaar" class="text-xs text-gray-500">
                    Eigenaar: {{ tile.eigenaar }}
                </p>
            </div>
        </template>

        <div
            v-if="tile?.resolved?.display === 'value' && tile?.valueFormatted"
            class="mb-4 rounded-md bg-gray-50 px-3 py-2"
        >
            <p class="text-2xl font-semibold text-gray-900">{{ tile.valueFormatted }}</p>
            <p v-if="tile.standPer" class="text-xs text-gray-500">
                Stand: {{ tile.standPer }}
            </p>
        </div>

        <div v-if="tile?.trendSeries?.length" class="mb-4">
            <h3 class="mb-2 text-sm font-semibold text-gray-900">
                Trend
            </h3>
            <KpiTegelGrafiek
                :series="tile.trendSeriesAll ?? tile.trendSeries"
                :periode="tile.trendPeriode ?? 'all'"
                :kpi-code="tile.kpiCode"
                :eenheid="tile.eenheid ?? 'ratio'"
                :richting="tile.richting"
                :doel="tile.doel"
                height-class="h-48"
                assen
            />
        </div>

        <div v-if="tile?.oordeelRow?.definitie" class="mb-4 text-sm text-gray-700">
            <h3 class="mb-1 font-semibold text-gray-900">Definitie</h3>
            <p>{{ tile.oordeelRow.definitie }}</p>
        </div>

        <div
            v-if="tile?.oordeelRow?.kanttekening"
            class="mb-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950"
        >
            <h3 class="mb-1 font-semibold">Kanttekening</h3>
            <p>{{ tile.oordeelRow.kanttekening }}</p>
        </div>

        <div
            v-if="tile?.oordeelRow?.aanname"
            class="mb-4 rounded-md border border-awc-orange/30 bg-awc-orange/5 p-3 text-sm"
        >
            <h3 class="mb-1 font-semibold text-awc-orange">Aanname</h3>
            <p>{{ tile.oordeelRow.aanname }}</p>
        </div>

        <div v-if="metaRows.length" class="mb-4">
            <h3 class="mb-2 text-sm font-semibold text-gray-900">
                Waar komt dit cijfer vandaan
            </h3>
            <dl class="grid grid-cols-[minmax(0,8rem)_1fr] gap-x-3 gap-y-1 text-xs">
                <template v-for="([label, val], i) in metaRows" :key="i">
                    <dt class="text-gray-500">{{ label }}</dt>
                    <dd class="text-gray-900">{{ val }}</dd>
                </template>
            </dl>
        </div>

        <div v-if="loading" class="flex justify-center py-8">
            <ProgressSpinner style="width: 2rem; height: 2rem" />
        </div>
        <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>

        <div v-else class="space-y-6">
            <KpiDrillTabel
                v-for="(rows, viewName) in tables"
                :key="viewName"
                :view="String(viewName)"
                :rows="rows"
                :meta="tableMeta[viewName] ?? null"
            />
        </div>

        <Link
            v-if="toonAfcAnalyse"
            :href="route('kpi.afc.analyse')"
            class="mt-6 inline-flex items-center gap-1 text-sm font-medium text-awc-orange hover:underline"
        >
            Verder in de AFC-analyse
            <i class="pi pi-arrow-right text-xs" aria-hidden="true" />
        </Link>

        <template #footer>
            <button
                type="button"
                class="text-sm text-gray-600 hover:text-gray-900"
                @click="close"
            >
                Sluiten
            </button>
        </template>
    </Drawer>
</template>
