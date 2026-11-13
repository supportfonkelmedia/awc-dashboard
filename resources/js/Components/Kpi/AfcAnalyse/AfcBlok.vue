<script setup>
import AfcInfo from '@/Components/Kpi/KpiInfo.vue';

defineProps({
    titel: { type: String, required: true },
    /** Uitleg achter het info-icoon; string of lijst alinea's. */
    uitleg: { type: [String, Array], default: null },
    /** Welk actief filter hier niet geldt, bijv. 'Richting geldt hier niet'. Alleen meegeven als er een filter aan staat. */
    geldtNiet: { type: String, default: null },
});
</script>

<template>
    <section class="rounded-xl border border-gray-200 bg-white p-5 lg:p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
            <h2 class="flex items-center gap-1.5 text-base font-semibold text-gray-900">
                {{ titel }}
                <AfcInfo v-if="uitleg" :tekst="uitleg" />
                <span
                    v-if="geldtNiet"
                    class="ml-1 rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600 ring-1 ring-gray-200"
                >
                    {{ geldtNiet }}
                </span>
            </h2>
            <div v-if="$slots.acties" class="flex flex-wrap items-center gap-3">
                <slot name="acties" />
            </div>
        </div>
        <div class="mt-4">
            <slot />
        </div>
    </section>
</template>
