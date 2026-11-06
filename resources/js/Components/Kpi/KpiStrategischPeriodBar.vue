<script setup>
/**
 * PERIODE (mockup 01): alleen de grafieken volgen de gekozen periode;
 * elke tegel houdt zijn vaste venster (Overdracht: kpi_oordeel heeft één rij per KPI/scope).
 */
defineProps({
    /** 'all' of jaartal */
    modelValue: {
        type: String,
        default: 'all',
    },
    /** Jaartallen aanwezig in kpi_trend, nieuwste eerst */
    years: {
        type: Array,
        default: () => [],
    },
});

const emit = defineEmits(['update:modelValue']);
</script>

<template>
    <div
        class="flex flex-wrap items-center justify-between gap-3 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-600 shadow-sm"
    >
        <label class="flex items-center gap-2">
            <span class="text-xs font-semibold uppercase tracking-wide text-gray-500">
                Periode
            </span>
            <select
                :value="modelValue"
                class="w-28 rounded border border-gray-300 bg-white py-1 pl-2 pr-8 text-sm text-gray-800 focus:border-[#ff7020] focus:outline-none focus:ring-1 focus:ring-[#ff7020]"
                @change="emit('update:modelValue', $event.target.value)"
            >
                <option value="all">Alles</option>
                <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
            </select>
        </label>
        <p class="text-xs text-gray-500">
            Grafieken volgen de gekozen periode. Elke tegel heeft een vast venster, dat staat
            onderaan de tegel.
        </p>
    </div>
</template>
