<script setup>
import { computed } from 'vue';

const props = defineProps({
    title: {
        type: String,
        required: true,
    },
});

const parts = computed(() => {
    const idx = props.title.indexOf(':');

    if (idx === -1) {
        return { lead: props.title, rest: null };
    }

    return {
        lead: props.title.slice(0, idx).trim(),
        rest: props.title.slice(idx + 1).trim(),
    };
});
</script>

<template>
    <div class="col-span-full mt-4">
        <p class="text-[11px] font-semibold uppercase tracking-wider text-[#ff7020]">
            {{ parts.lead }}
        </p>
        <h2 v-if="parts.rest" class="mt-0.5 text-xl font-bold text-gray-900">
            {{ parts.rest }}
        </h2>
    </div>
</template>
