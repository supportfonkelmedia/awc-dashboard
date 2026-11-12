<script setup>
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';

defineProps({
    /** [{ key, label, fmt?: (v, row) => string, rechts?: boolean, klasse?: (row) => string }] */
    kolommen: { type: Array, required: true },
    rijen: { type: Array, required: true },
    sorteerbaar: { type: Boolean, default: false },
    sorteerVeld: { type: String, default: null },
    leegTekst: { type: String, default: 'Geen gegevens voor deze keuze.' },
    rijKlasse: { type: Function, default: null },
});
</script>

<template>
    <div class="overflow-x-auto">
        <DataTable
            :value="rijen"
            size="small"
            :sort-field="sorteerVeld ?? undefined"
            :sort-order="sorteerVeld ? -1 : undefined"
            :row-class="rijKlasse ?? undefined"
            class="afc-tabel text-sm"
        >
            <template #empty>
                <p class="py-3 text-sm text-gray-500">{{ leegTekst }}</p>
            </template>
            <Column
                v-for="k in kolommen"
                :key="k.key"
                :field="k.key"
                :header="k.label"
                :sortable="sorteerbaar"
                :header-class="k.rechts ? 'afc-rechts' : ''"
                :body-class="k.rechts ? 'text-right tabular-nums' : ''"
            >
                <template #body="{ data }">
                    <span :class="k.klasse ? k.klasse(data) : ''">
                        {{ k.fmt ? k.fmt(data[k.key], data) : data[k.key] }}
                    </span>
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<style scoped>
.afc-tabel :deep(.afc-rechts .p-datatable-column-header-content) {
    justify-content: flex-end;
}
.afc-tabel :deep(th) {
    font-size: 12px;
    font-weight: 500;
    color: #525252;
    white-space: nowrap;
}
.afc-tabel :deep(.afc-totaal td) {
    font-weight: 600;
    border-top: 1px solid #d4d4d4;
}
</style>
