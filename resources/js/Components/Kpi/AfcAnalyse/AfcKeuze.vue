<script setup>
const model = defineModel({ type: [String, Number], required: true });

defineProps({
    label: { type: String, required: true },
    /** [{ value, label }] */
    opties: { type: Array, required: true },
});
</script>

<template>
    <label class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">{{ label }}</span>
        <select
            :value="model"
            class="rounded border border-gray-300 bg-white py-1 pl-2 pr-8 text-sm text-gray-800 focus:border-awc-orange focus:outline-none focus:ring-1 focus:ring-awc-orange"
            @change="model = typeof model === 'number' ? Number($event.target.value) : $event.target.value"
        >
            <option v-for="o in opties" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
    </label>
</template>
