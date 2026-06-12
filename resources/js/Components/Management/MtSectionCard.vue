<script setup>
import Card from 'primevue/card';

defineProps({
    title: { type: String, required: true },
    subtitle: { type: String, default: '' },
    accent: { type: Boolean, default: true },
});

const cardPt = {
    root: { class: 'border border-gray-100 shadow-sm bg-white' },
    body: { class: '!p-0' },
    title: { class: '!px-5 !pt-5 !pb-0' },
    content: { class: '!px-5 !pb-5 !pt-4' },
};
</script>

<template>
    <Card :pt="cardPt">
        <template #title>
            <div>
                <h2
                    class="text-xs font-semibold uppercase tracking-wider"
                    :class="accent ? 'text-[#ff7020]' : 'text-gray-600'"
                >
                    {{ title }}
                </h2>
                <p
                    v-if="subtitle"
                    class="mt-1 text-xs font-normal normal-case tracking-normal text-gray-500"
                >
                    {{ subtitle }}
                </p>
            </div>
        </template>
        <template #content>
            <slot />
        </template>
    </Card>
</template>
