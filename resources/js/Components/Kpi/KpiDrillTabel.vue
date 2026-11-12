<script setup>
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import { computed, ref, watch } from 'vue';
import {
    drillColumnHeader,
    drillKolommen,
    drillViewTitel,
    drillWaarde,
} from '@/utils/kpiDrillColumns';

/**
 * Eén drill-tabel in de drawer: leesbare titel en kolommen, en voor de detail-drills
 * (rijen met een kolom `tegelvenster`) een keuze welk venster je ziet, standaard het venster
 * dat in de tegel telt. Telt ook hoeveel rijen op een bulkdag vallen.
 */
const props = defineProps({
    view: { type: String, required: true },
    rows: { type: Array, default: () => [] },
    /** table_meta[view] uit de handler: row_count, truncated, total_count. */
    meta: { type: Object, default: null },
});

const vensters = computed(() => {
    if (!props.rows.length || !('tegelvenster' in props.rows[0])) {
        return [];
    }

    return [...new Set(props.rows.map((r) => String(r.tegelvenster ?? '')))];
});

const venster = ref('');
watch(
    vensters,
    (v) => {
        venster.value = v[0] ?? '';
    },
    { immediate: true },
);

/**
 * Maanden na de huidige maand bestaan alleen door vooruitgedateerde boekingen (bijv. december-INK
 * in november). Die horen niet bovenaan een maandtabel; we verbergen ze en zeggen dat erbij.
 */
const huidigeMaand = (() => {
    const d = new Date();

    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
})();
const isToekomst = (r) =>
    typeof r.maand === 'string' && r.maand.slice(0, 10) > huidigeMaand;
const toekomst = computed(() => props.rows.filter(isToekomst).length);

const zichtbaar = computed(() =>
    (venster.value
        ? props.rows.filter((r) => String(r.tegelvenster ?? '') === venster.value)
        : props.rows
    ).filter((r) => !isToekomst(r)),
);

const kolommen = computed(() =>
    drillKolommen(zichtbaar.value).filter((k) => !(vensters.value.length && k === 'tegelvenster')),
);

const samenvatting = computed(() => {
    const n = zichtbaar.value.length;
    if (!n || !('bulkdag' in zichtbaar.value[0])) {
        return null;
    }
    const bulk = zichtbaar.value.filter((r) => r.bulkdag === true).length;
    const uitkomsten = 'uitkomst' in zichtbaar.value[0]
        ? ['gewonnen', 'verloren']
              .map((u) => [u, zichtbaar.value.filter((r) => r.uitkomst === u).length])
              .filter(([, c]) => c > 0)
              .map(([u, c]) => `${c} ${u}`)
        : [];

    return [`${n} ${n === 1 ? 'rij' : 'rijen'}`, ...uitkomsten, bulk ? `${bulk} op een bulkdag` : null]
        .filter(Boolean)
        .join(' · ');
});

const afgekapt = computed(() =>
    props.meta?.truncated
        ? `Eerste ${props.meta.row_count} van ${props.meta.total_count ?? 'meer'} rijen.`
        : null,
);
</script>

<template>
    <div>
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-sm font-semibold text-gray-900" :title="view">
                {{ drillViewTitel(view) }}
            </h3>
            <select
                v-if="vensters.length > 1"
                v-model="venster"
                class="rounded-md border border-gray-300 py-1 pl-2 pr-7 text-xs text-gray-700"
                :aria-label="`Venster voor ${drillViewTitel(view)}`"
            >
                <option v-for="v in vensters" :key="v" :value="v">{{ v }}</option>
            </select>
        </div>
        <p v-if="samenvatting" class="mb-2 text-xs text-gray-600">{{ samenvatting }}</p>
        <DataTable
            v-if="zichtbaar.length"
            :value="zichtbaar"
            size="small"
            scrollable
            scroll-height="280px"
            class="text-xs"
        >
            <Column
                v-for="col in kolommen"
                :key="col"
                :field="col"
                :header="drillColumnHeader(col)"
            >
                <template #body="{ data }">{{ drillWaarde(data[col]) }}</template>
            </Column>
        </DataTable>
        <p v-else class="text-sm text-gray-500">Geen rijen.</p>
        <p v-if="afgekapt" class="mt-1 text-xs text-gray-500">{{ afgekapt }}</p>
        <p v-if="toekomst" class="mt-1 text-xs text-gray-500">
            {{ toekomst }} {{ toekomst === 1 ? 'rij' : 'rijen' }} met een maand na deze maand verborgen
            (vooruitgedateerde boekingen).
        </p>
    </div>
</template>
