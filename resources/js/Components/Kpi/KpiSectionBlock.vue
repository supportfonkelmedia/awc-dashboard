<script setup>
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Button from 'primevue/button';
import { computed } from 'vue';

const emit = defineEmits(['open-invoer']);

const props = defineProps({
    section: {
        type: Object,
        required: true,
    },
    payload: {
        type: Object,
        default: null,
    },
    gepland2027: {
        type: Array,
        default: () => [],
    },
});

const waardeBron = computed(() =>
    String(props.section.configRow?.waarde_bron ?? ''),
);

const title = computed(() => props.section.titel || props.section.pijler);

const controlesRows = computed(() => props.payload?.kpi_controles ?? []);

const handmatigRegistryRows = computed(() => {
    const reg = props.payload?.kpi_registry ?? [];

    return reg.filter((r) => String(r.bouwstatus ?? '') === 'handmatig');
});

const statusDotClass = (status) => {
    const s = String(status ?? '').toLowerCase();
    if (s === 'fout') {
        return 'bg-red-500';
    }
    if (s === 'let_op') {
        return 'bg-amber-500';
    }

    return 'bg-emerald-500';
};
</script>

<template>
    <section
        :id="waardeBron === 'kpi_controles' ? 'datakwaliteit' : undefined"
        class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
    >
        <div class="flex flex-wrap items-center justify-between gap-2">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-900">
                {{ title }}
            </h2>
            <Button
                v-if="waardeBron === 'kpi_registry'"
                label="Handmatige invoer"
                size="small"
                icon="pi pi-pencil"
                @click="emit('open-invoer')"
            />
        </div>
        <p
            v-if="section.configRow?.vaste_tekst"
            class="mt-1 text-sm text-gray-600"
        >
            {{ section.configRow.vaste_tekst }}
        </p>

        <DataTable
            v-if="waardeBron === 'kpi_controles' && controlesRows.length"
            :value="controlesRows"
            size="small"
            class="mt-4 text-sm"
            striped-rows
        >
            <Column header="" style="width: 2rem">
                <template #body="{ data }">
                    <span
                        class="inline-block h-2.5 w-2.5 rounded-full"
                        :class="statusDotClass(data.status)"
                    />
                </template>
            </Column>
            <Column field="controle" header="Controle" />
            <Column field="waarde" header="Uitkomst" />
            <Column field="norm" header="Norm" />
            <Column field="toelichting" header="Wat het betekent" />
        </DataTable>

        <DataTable
            v-else-if="waardeBron === 'kpi_registry' && handmatigRegistryRows.length"
            :value="handmatigRegistryRows"
            size="small"
            class="mt-4 text-sm"
        >
            <Column field="naam" header="KPI" />
            <Column field="eigenaar" header="Door" />
            <Column field="updatefrequentie" header="Ritme" />
        </DataTable>

        <ul
            v-else-if="
                gepland2027.length &&
                (section.titel?.includes('2027') ||
                    section.titel?.toLowerCase().includes('gepland'))
            "
            class="mt-4 space-y-2 text-sm text-gray-700"
        >
            <li v-for="row in gepland2027" :key="row.kpi_code">
                <strong>{{ row.naam }}</strong> — {{ row.leeg_reden }}
            </li>
        </ul>

        <p v-else class="mt-4 text-sm text-gray-500">
            Geen rijen voor deze sectie in de huidige payload.
        </p>
    </section>
</template>
