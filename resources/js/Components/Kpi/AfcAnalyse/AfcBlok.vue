<script setup>
defineProps({
    titel: { type: String, required: true },
    intro: { type: String, default: null },
    voetnoot: { type: String, default: null },
});
</script>

<template>
    <section class="rounded-xl border border-gray-200 bg-white p-5 lg:p-6">
        <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0 max-w-3xl">
                <h2 class="text-base font-semibold text-gray-900">{{ titel }}</h2>
                <p v-if="intro" class="mt-1 text-sm leading-relaxed text-gray-600">{{ intro }}</p>
            </div>
            <div v-if="$slots.acties" class="flex flex-wrap items-center gap-3">
                <slot name="acties" />
            </div>
        </div>
        <div class="mt-4">
            <slot />
        </div>
        <p v-if="voetnoot" class="mt-3 max-w-3xl text-xs leading-relaxed text-gray-500">{{ voetnoot }}</p>
    </section>
</template>
