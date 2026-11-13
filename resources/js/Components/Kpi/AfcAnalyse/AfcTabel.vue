<script setup>
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import { computed, ref } from 'vue';

const props = defineProps({
    /** [{ key, label, fmt?: (v, row) => string, rechts?: boolean, klasse?: (row) => string, stip?: (row) => string|null }] */
    kolommen: { type: Array, required: true },
    rijen: { type: Array, required: true },
    sorteerbaar: { type: Boolean, default: false },
    sorteerVeld: { type: String, default: null },
    leegTekst: { type: String, default: 'Geen gegevens voor deze keuze.' },
    rijKlasse: { type: Function, default: null },
    /** Toon eerst zoveel rijen, met een knop voor de rest. */
    beperk: { type: Number, default: null },
});

// Zelf sorteren: dan sorteert een ingeklapte tabel over álle rijen, niet alleen over de zichtbare.
const veld = ref(props.sorteerVeld);
const volgorde = ref(props.sorteerVeld ? -1 : 0);
const alles = ref(false);

function vergelijk(a, b) {
    const leegA = a == null || a === '';
    const leegB = b == null || b === '';
    if (leegA || leegB) {
        return leegA === leegB ? 0 : leegA ? 1 : -1;
    }
    const na = Number(a);
    const nb = Number(b);
    if (!Number.isNaN(na) && !Number.isNaN(nb)) {
        return na - nb;
    }

    return String(a).localeCompare(String(b), 'nl');
}

const gesorteerd = computed(() => {
    if (!veld.value || !volgorde.value) {
        return props.rijen;
    }
    const v = veld.value;

    // Lege waarden blijven onderaan, ook bij omgekeerd sorteren.
    return [...props.rijen].sort((x, y) => {
        const leeg = (r) => r[v] == null || r[v] === '';
        if (leeg(x) !== leeg(y)) {
            return leeg(x) ? 1 : -1;
        }

        return volgorde.value * vergelijk(x[v], y[v]);
    });
});

const ingeklapt = computed(() => props.beperk != null && !alles.value && props.rijen.length > props.beperk);
const zichtbaar = computed(() => (ingeklapt.value ? gesorteerd.value.slice(0, props.beperk) : gesorteerd.value));

function opSorteer(e) {
    veld.value = e.sortField;
    volgorde.value = e.sortOrder ?? 0;
}
</script>

<template>
    <div>
        <div class="overflow-x-auto">
            <DataTable
                :value="zichtbaar"
                size="small"
                lazy
                :sort-field="veld ?? undefined"
                :sort-order="volgorde || undefined"
                removable-sort
                :row-class="rijKlasse ?? undefined"
                class="afc-tabel text-sm"
                @sort="opSorteer"
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
                    :body-class="k.rechts ? 'afc-rechts-cel' : ''"
                >
                    <template #body="{ data }">
                        <span :class="['inline-flex items-center gap-1.5', k.klasse ? k.klasse(data) : '']">
                            <span
                                v-if="k.stip && k.stip(data)"
                                class="inline-block h-2 w-2 shrink-0 rounded-sm"
                                :style="{ background: k.stip(data) }"
                            />
                            {{ k.fmt ? k.fmt(data[k.key], data) : data[k.key] }}
                        </span>
                    </template>
                </Column>
            </DataTable>
        </div>
        <button
            v-if="beperk != null && rijen.length > beperk"
            type="button"
            class="mt-2 text-xs font-medium text-gray-600 underline-offset-2 hover:text-gray-900 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-awc-orange"
            @click="alles = !alles"
        >
            {{ alles ? `Toon alleen de eerste ${beperk}` : `Toon alle ${rijen.length}` }}
        </button>
    </div>
</template>

<style scoped>
.afc-tabel :deep(.afc-rechts .p-datatable-column-header-content) {
    justify-content: flex-end;
}
/* Het PrimeVue-thema zet text-align op de cel; een utility-klasse wint daar niet van. */
.afc-tabel :deep(td.afc-rechts-cel) {
    text-align: right;
    font-variant-numeric: tabular-nums;
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
