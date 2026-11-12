<script setup>
/**
 * PERIODE (mockup 01): alleen de grafieken volgen de gekozen periode;
 * elke tegel houdt zijn vaste venster (Overdracht: kpi_oordeel heeft één rij per KPI/scope).
 *
 * ENTITEIT (feedback MT 10-11-2026): tegels die per entiteit bestaan, wisselen naar
 * AWC, AFC of ACC. De rest blijft staan met een notitie op de tegel.
 */
import { KPI_ENTITEITEN } from '@/constants/kpiEntiteiten';

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
    /** scope_code van de gekozen entiteit, of 'concern' */
    entiteit: {
        type: String,
        default: 'concern',
    },
});

const emit = defineEmits(['update:modelValue', 'update:entiteit']);
</script>

<template>
    <div
        class="flex flex-wrap items-center justify-between gap-3 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-600 shadow-sm"
    >
        <div class="flex flex-wrap items-center gap-x-5 gap-y-2">
            <label class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-700">
                    Periode
                </span>
                <select
                    :value="modelValue"
                    class="w-28 rounded border border-gray-300 bg-white py-1 pl-2 pr-8 text-sm text-gray-800 focus:border-awc-orange focus:outline-none focus:ring-1 focus:ring-awc-orange"
                    @change="emit('update:modelValue', $event.target.value)"
                >
                    <option value="all">Alles</option>
                    <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
                </select>
            </label>

            <div class="flex items-center gap-2">
                <span
                    id="kpi-entiteit-label"
                    class="text-sm font-medium text-gray-700"
                >
                    Entiteit
                </span>
                <div
                    role="group"
                    aria-labelledby="kpi-entiteit-label"
                    class="inline-flex overflow-hidden rounded border border-gray-300"
                >
                    <button
                        v-for="(e, i) in KPI_ENTITEITEN"
                        :key="e.scope"
                        type="button"
                        :aria-pressed="entiteit === e.scope"
                        class="px-2.5 py-1 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-awc-orange"
                        :class="[
                            i > 0 ? 'border-l border-gray-300' : '',
                            entiteit === e.scope
                                ? 'bg-awc-orange font-semibold text-white'
                                : 'bg-white text-gray-700 hover:bg-gray-50',
                        ]"
                        @click="emit('update:entiteit', e.scope)"
                    >
                        {{ e.label }}
                    </button>
                </div>
            </div>
        </div>
        <p class="text-xs text-gray-500">
            Grafieken volgen de gekozen periode. Elke tegel heeft een vast venster, dat staat
            onderaan de tegel.
        </p>
    </div>
</template>
