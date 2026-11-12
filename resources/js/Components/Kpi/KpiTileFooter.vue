<script setup>
import KpiInfo from '@/Components/Kpi/KpiInfo.vue';
import { computed } from 'vue';

/**
 * Voet: stand links met venster en bron achter een info-icoon, Details rechts.
 */
const props = defineProps({
    tile: {
        type: Object,
        required: true,
    },
    showDetails: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(['details', 'feedback']);

const bronUitleg = computed(() =>
    [props.tile.venster, props.tile.bronLabel ? `Bron: ${props.tile.bronLabel}` : ''].filter(Boolean),
);
</script>

<template>
    <footer
        class="mt-3 flex items-center justify-between gap-3 border-t border-gray-100 px-4 py-2.5"
    >
        <div class="flex min-w-0 items-center gap-1 text-[10px] leading-[1.5] text-gray-500">
            <span v-if="tile.standPer" class="truncate">Stand {{ tile.standPer }}</span>
            <span v-else-if="tile.bronLabel" class="truncate">{{ tile.bronLabel }}</span>
            <KpiInfo v-if="bronUitleg.length" :tekst="bronUitleg" :label="`Venster en bron van ${tile.titel ?? 'deze tegel'}`" />
        </div>
        <div class="flex shrink-0 items-center gap-1.5">
            <button
                type="button"
                class="inline-flex h-7 w-7 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-awc-orange"
                :aria-label="`Feedback over ${tile.titel ?? 'deze tegel'}`"
                title="Feedback over deze tegel"
                @click="emit('feedback')"
            >
                <i class="pi pi-comment text-[12px]" aria-hidden="true" />
            </button>
            <button
                v-if="showDetails"
                type="button"
                class="inline-flex shrink-0 items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-[11px] font-medium text-gray-800 hover:bg-gray-50"
                @click="emit('details')"
            >
                Details
                <i class="pi pi-angle-right text-[11px]" aria-hidden="true" />
            </button>
        </div>
    </footer>
</template>
