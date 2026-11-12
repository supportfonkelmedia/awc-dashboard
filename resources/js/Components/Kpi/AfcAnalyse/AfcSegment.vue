<script setup>
const model = defineModel({ type: String, required: true });

defineProps({
    label: { type: String, required: true },
    /** [{ value, label }] */
    opties: { type: Array, required: true },
});

const id = `afc-seg-${Math.random().toString(36).slice(2, 8)}`;
</script>

<template>
    <div class="flex items-center gap-2">
        <span :id="id" class="text-sm font-medium text-gray-700">{{ label }}</span>
        <div role="group" :aria-labelledby="id" class="inline-flex overflow-hidden rounded border border-gray-300">
            <button
                v-for="(o, i) in opties"
                :key="o.value"
                type="button"
                :aria-pressed="model === o.value"
                class="px-2.5 py-1 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-awc-orange"
                :class="[
                    i > 0 ? 'border-l border-gray-300' : '',
                    model === o.value
                        ? 'bg-awc-orange font-semibold text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50',
                ]"
                @click="model = o.value"
            >
                {{ o.label }}
            </button>
        </div>
    </div>
</template>
