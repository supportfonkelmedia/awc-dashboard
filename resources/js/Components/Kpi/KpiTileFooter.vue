<script setup>
/**
 * Mockup footer: venster / "Bron: … · stand …" lines left, Details button right.
 */
defineProps({
    tile: {
        type: Object,
        required: true,
    },
    showDetails: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(['details']);
</script>

<template>
    <footer
        class="mt-3 flex items-center justify-between gap-3 border-t border-gray-100 px-4 py-2.5"
    >
        <div class="min-w-0 text-[10px] leading-[1.5] text-gray-500">
            <p v-if="tile.venster" class="truncate">{{ tile.venster }}</p>
            <p v-if="tile.bronLabel || tile.standPer" class="flex items-center gap-1 truncate">
                <i class="pi pi-database text-[9px]" aria-hidden="true" />
                <span class="truncate">
                    <span v-if="tile.bronLabel">Bron: {{ tile.bronLabel }}</span>
                    <span v-if="tile.bronLabel && tile.standPer"> · </span>
                    <span v-if="tile.standPer">stand {{ tile.standPer }}</span>
                </span>
            </p>
        </div>
        <button
            v-if="showDetails"
            type="button"
            class="inline-flex shrink-0 items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-[11px] font-medium text-gray-800 hover:bg-gray-50"
            @click="emit('details')"
        >
            Details
            <i class="pi pi-angle-right text-[11px]" aria-hidden="true" />
        </button>
    </footer>
</template>
