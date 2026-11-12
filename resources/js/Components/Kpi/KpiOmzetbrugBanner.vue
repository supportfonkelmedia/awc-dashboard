<script setup>
import { leesbaar } from '@/utils/leesbaar';
import KpiTileFooter from '@/Components/Kpi/KpiTileFooter.vue';
import { fetchKpiDrill } from '@/composables/useKpiDrillFetch';
import ProgressSpinner from 'primevue/progressspinner';
import { computed, onMounted, ref } from 'vue';
import { fmtEuroValue } from '@/utils/kpiFormat';

const props = defineProps({
    tile: {
        type: Object,
        required: true,
    },
    /** Rows from screen bundle (kpi_omzetbrug); skips extra drill request when set. */
    prefetchedRows: {
        type: Array,
        default: null,
    },
});

const emit = defineEmits(['details', 'feedback']);

const loading = ref(true);
const error = ref(null);
/** @type {import('vue').Ref<Array<Record<string, unknown>>>} */
const bridgeRows = ref([]);

const FLOW_ORDER = [
    'start',
    'nieuw',
    'gegroeid',
    'gekrompen',
    'verloren',
    'eind',
];

const FLOW_LABELS = {
    start: 'Omzet vorige 12 maanden',
    nieuw: 'Nieuwe klanten',
    gegroeid: 'Gegroeid',
    gekrompen: 'Gekrompen',
    verloren: 'Verloren klanten',
    eind: 'Omzet laatste 12 maanden',
};

function applyScopeFilter(rows) {
    const scopeMap = {
        concern: 'Concern',
        alaw: 'AWC',
        pgl1: 'AFC',
        acco: 'ACC',
    };
    const targetScope =
        scopeMap[props.tile.scopeCode] ?? props.tile.scopeCode ?? 'Concern';

    bridgeRows.value = rows.filter((r) => String(r.scope ?? '') === targetScope);
}

onMounted(async () => {
    loading.value = true;
    error.value = null;

    if (Array.isArray(props.prefetchedRows) && props.prefetchedRows.length) {
        applyScopeFilter(props.prefetchedRows);
        loading.value = false;

        return;
    }

    const { tables, error: err } = await fetchKpiDrill(['kpi_omzetbrug']);
    loading.value = false;
    if (err) {
        error.value = err;

        return;
    }
    applyScopeFilter(tables.kpi_omzetbrug ?? []);
});

const flowSegments = computed(() => {
    const map = new Map();
    for (const row of bridgeRows.value) {
        map.set(String(row.component), row);
    }

    return FLOW_ORDER.filter((c) => map.has(c)).map((component) => {
        const row = map.get(component);
        const bedrag = Number(row?.bedrag ?? 0);

        return {
            component,
            label: FLOW_LABELS[component] ?? component,
            row,
            bedrag,
            isTotal: component === 'start' || component === 'eind',
            isPositive: component === 'nieuw' || component === 'gegroeid',
            isNegative: component === 'gekrompen' || component === 'verloren',
        };
    });
});

/**
 * Waterfall rows (mockup 01): totals as full bars from 0, deltas as floating
 * bars positioned at the running cumulative value.
 */
const waterfallRows = computed(() => {
    const segs = flowSegments.value;
    const start = segs.find((s) => s.component === 'start');
    let running = start ? start.bedrag : 0;
    let scaleMax = 1;
    const rows = [];

    for (const seg of segs) {
        let from;
        let to;
        if (seg.isTotal) {
            from = 0;
            to = seg.bedrag;
            if (seg.component === 'eind') {
                running = seg.bedrag;
            }
        } else {
            from = running;
            to = running + seg.bedrag;
            running = to;
        }
        const lo = Math.min(from, to);
        const hi = Math.max(from, to);
        scaleMax = Math.max(scaleMax, hi);
        rows.push({ ...seg, lo, hi });
    }

    return rows.map((r) => ({
        ...r,
        leftPct: (r.lo / scaleMax) * 100,
        widthPct: Math.max(0.6, ((r.hi - r.lo) / scaleMax) * 100),
    }));
});

function fmtBedrag(seg) {
    if (seg.row?.bedrag == null) {
        return 'n.b.';
    }
    const v = Number(seg.row.bedrag);
    if (seg.isTotal) {
        return fmtEuroValue(v);
    }
    const sign = v > 0 ? '+' : v < 0 ? '−' : '';

    return `${sign}${fmtEuroValue(Math.abs(v)).replace(/^−/, '')}`;
}

function rowLabel(seg) {
    const n = seg.row?.klanten;

    return n != null && !seg.isTotal ? `${seg.label} (${n})` : seg.label;
}

function barClass(seg) {
    if (seg.component === 'start') {
        return 'bg-gray-400';
    }
    if (seg.component === 'eind') {
        return 'bg-gray-900';
    }
    if (seg.isPositive) {
        return 'bg-emerald-700';
    }
    if (seg.isNegative) {
        return 'bg-red-600';
    }

    return 'bg-gray-400';
}

function valueClass(seg) {
    if (seg.isTotal) {
        return 'text-gray-900';
    }
    if (seg.isPositive) {
        return 'text-emerald-700';
    }
    if (seg.isNegative) {
        return 'text-red-600';
    }

    return 'text-gray-600';
}
</script>

<template>
    <article
        class="flex flex-col rounded-xl border border-gray-200 bg-white md:col-span-2"
    >
        <div class="flex items-start justify-between gap-4 px-4 pt-3.5">
            <div>
                <p class="text-[11px] text-gray-500">
                    {{ leesbaar(tile.themeLabel || 'Waarde') }}
                </p>
                <h3 class="mt-1 text-[13px] font-bold text-gray-900">
                    {{ tile.titel }}
                </h3>
            </div>
            <div class="text-right">
                <p
                    v-if="tile.valueFormatted"
                    class="text-lg font-bold leading-tight text-gray-900"
                >
                    {{ tile.valueFormatted }}
                </p>
                <p
                    v-if="tile.deltaFormatted"
                    class="text-[11px] font-semibold"
                    :class="
                        tile.deltaTone === 'good'
                            ? 'text-emerald-600'
                            : tile.deltaTone === 'bad'
                              ? 'text-red-600'
                              : 'text-gray-500'
                    "
                >
                    <span v-if="tile.deltaTone === 'good'">▲</span>
                    <span v-else-if="tile.deltaTone === 'bad'">▼</span>
                    {{ tile.deltaFormatted }}
                </p>
            </div>
        </div>

        <div class="px-4 pb-2 pt-4">
            <div v-if="loading" class="flex justify-center py-8">
                <ProgressSpinner style="width: 2rem; height: 2rem" />
            </div>
            <p v-else-if="error" class="text-sm text-amber-700">{{ error }}</p>
            <p v-else-if="!flowSegments.length" class="text-sm text-gray-500">
                Geen omzetbrug-rijen voor deze scope.
            </p>
            <div v-else class="space-y-2">
                <div
                    v-for="seg in waterfallRows"
                    :key="seg.component"
                    class="grid grid-cols-[minmax(9rem,11rem)_1fr_auto] items-center gap-3"
                >
                    <span class="truncate text-xs text-gray-600">{{ rowLabel(seg) }}</span>
                    <div class="relative h-2.5 w-full rounded-sm bg-gray-100">
                        <div
                            class="absolute inset-y-0 rounded-sm"
                            :class="barClass(seg)"
                            :style="{ left: `${seg.leftPct}%`, width: `${seg.widthPct}%` }"
                        />
                    </div>
                    <span
                        class="min-w-[5.5rem] text-right text-xs font-semibold tabular-nums"
                        :class="valueClass(seg)"
                    >
                        {{ fmtBedrag(seg) }}
                    </span>
                </div>
            </div>
        </div>

        <KpiTileFooter
            class="mt-auto"
            :tile="tile"
            :show-details="Boolean(tile.drillViews?.length)"
            @details="emit('details', tile)"
            @feedback="emit('feedback', tile)"
        />
    </article>
</template>
