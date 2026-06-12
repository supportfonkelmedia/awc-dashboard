<script setup>
import { FINANCE_DRAWER_COLUMNS } from '@/composables/useMtKpiData';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Drawer from 'primevue/drawer';
import { computed } from 'vue';

const visible = defineModel('visible', { type: Boolean, default: false });

const props = defineProps({
    kpi: {
        type: Object,
        default: null,
    },
    rows: {
        type: Array,
        default: () => [],
    },
    periodLabel: {
        type: String,
        default: '',
    },
});

const columns = computed(() => {
    const id = props.kpi?.id;
    return id ? (FINANCE_DRAWER_COLUMNS[id] ?? []) : [];
});

const emptyMessage = computed(() => {
    if (!props.kpi) return 'Geen data.';
    return `Geen Cashweb-data voor ${props.kpi.title} in deze periode.`;
});
</script>

<template>
    <Drawer
        v-model:visible="visible"
        position="right"
        class="finance-kpi-drawer !w-[min(42rem,95vw)]"
        :pt="{
            root: { class: '!shadow-2xl' },
            header: { class: '!border-b !border-gray-100 !pb-4' },
            content: { class: '!pt-4' },
        }"
    >
        <template #header>
            <div class="min-w-0 pr-2">
                <p
                    class="text-xs font-semibold uppercase tracking-wider text-[#ff7020]"
                >
                    Financiële bouwsteen
                </p>
                <h2 class="mt-1 text-lg font-bold text-gray-900">
                    {{ kpi?.title ?? 'Detail' }}
                </h2>
                <p
                    v-if="periodLabel"
                    class="mt-1 text-xs text-gray-500"
                >
                    {{ periodLabel }}
                </p>
            </div>
        </template>

        <div
            v-if="kpi"
            class="flex flex-col gap-4"
        >
            <div
                class="flex flex-wrap items-baseline gap-x-4 gap-y-1 rounded-lg border border-gray-100 bg-gray-50 px-4 py-3"
            >
                <span class="text-2xl font-bold text-gray-900">{{
                    kpi.value
                }}</span>
                <span
                    v-if="kpi.delta"
                    class="text-sm font-medium"
                    :class="
                        kpi.deltaPositive
                            ? 'text-emerald-600'
                            : 'text-red-600'
                    "
                >
                    {{ kpi.delta }}
                </span>
            </div>

            <p class="text-sm text-gray-600">
                <span class="font-medium text-gray-800">Berekening:</span>
                {{ kpi.calculation }}
            </p>
            <p
                v-if="kpi.footer"
                class="text-xs text-gray-500"
            >
                {{ kpi.footer }}
            </p>

            <DataTable
                :value="rows"
                striped-rows
                show-gridlines
                scrollable
                scroll-height="flex"
                sort-mode="single"
                removable-sort
                class="finance-kpi-table p-datatable-sm text-sm"
                :empty-message="emptyMessage"
            >
                <Column
                    v-for="col in columns"
                    :key="col.field"
                    :field="col.field"
                    :header="col.header"
                    sortable
                />
            </DataTable>
        </div>
    </Drawer>
</template>

<style scoped>
.finance-kpi-drawer :deep(.p-drawer-content) {
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.finance-kpi-table {
    flex: 1;
    min-height: 12rem;
}

.finance-kpi-table :deep(.p-datatable-table-container) {
    max-height: min(60vh, 28rem);
}
</style>
