<script setup>
/**
 * Operationeel mockup: fase-indicators (geen KPI-berekening).
 */
const phases = [
    { n: 1, title: 'Bewustwording', hint: '1 tegel · in opbouw' },
    { n: 2, title: 'Overweging', hint: '1 tegel · in opbouw' },
    { n: 3, title: 'Besluit', hint: '1 tegel · live' },
    { n: 4, title: 'Onboarding', hint: '1 tegel · live' },
    { n: 5, title: 'Adoptie', hint: '3 tegels · 1 live' },
    { n: 6, title: 'Retentie', hint: '2 tegels · 1 live' },
];
</script>

<template>
    <div
        class="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6"
        aria-label="Fases klantreis"
    >
        <div
            v-for="phase in phases"
            :key="phase.n"
            class="rounded-md border border-gray-200 bg-white px-3 py-2 text-center shadow-sm"
        >
            <p class="text-[11px] text-gray-400">Fase {{ phase.n }}</p>
            <p class="text-xs font-semibold text-gray-900">{{ phase.title }}</p>
            <p class="mt-0.5 text-[10px] text-gray-500">{{ phase.hint }}</p>
        </div>
    </div>
</template>
