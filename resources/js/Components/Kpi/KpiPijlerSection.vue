<script setup>
import { leesbaar } from '@/utils/leesbaar';
import { computed } from 'vue';

const props = defineProps({
    title: {
        type: String,
        required: true,
    },
});

// Van "AANVULLEND: Omzet en mensen" blijft "Omzet en mensen" over. Zonder
// dubbele punt wordt de hele titel in gewone zinsletters gezet.
const heading = computed(() => {
    const idx = props.title.indexOf(':');

    return leesbaar(idx === -1 ? props.title : props.title.slice(idx + 1));
});
</script>

<template>
    <div class="col-span-full mt-6">
        <h2 class="text-lg font-bold text-gray-900">
            {{ heading }}
        </h2>
    </div>
</template>
