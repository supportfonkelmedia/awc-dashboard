<script setup>
defineProps({
    label: { type: String, required: true },
    waarde: { type: String, default: '' },
    sub: { type: String, default: null },
    subKlasse: { type: String, default: 'text-gray-500' },
});
</script>

<template>
    <div class="flex flex-col rounded-xl border border-gray-200 bg-white p-4">
        <p class="text-xs text-gray-600">{{ label }}</p>
        <p class="mt-2 text-[26px] font-semibold tabular-nums leading-none tracking-tight text-gray-900">
            {{ waarde || 'geen data' }}
        </p>
        <p v-if="sub" class="mt-2 text-xs font-medium" :class="subKlasse">{{ sub }}</p>
        <div v-if="$slots.default" class="mt-auto pt-4">
            <slot />
        </div>
    </div>
</template>
