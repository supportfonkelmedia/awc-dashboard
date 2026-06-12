<script setup>
import { STATUS_LABELS, STATUS_TAG_SEVERITY } from '@/config/mtKpiFramework';
import Card from 'primevue/card';
import Tag from 'primevue/tag';
import { computed } from 'vue';

const props = defineProps({
    title: { type: String, required: true },
    theme: { type: String, default: '' },
    status: { type: String, required: true },
    value: { type: String, default: null },
    delta: { type: String, default: '' },
    deltaPositive: { type: Boolean, default: true },
    footer: { type: String, default: '' },
    note: { type: String, default: null },
    strategicLink: { type: String, default: null },
    compact: { type: Boolean, default: false },
    explainable: { type: Boolean, default: false },
});

const emit = defineEmits(['explain']);

const statusLabel = computed(() => STATUS_LABELS[props.status] ?? props.status);

const statusSeverity = computed(
    () => STATUS_TAG_SEVERITY[props.status] ?? 'secondary',
);

const cardPt = computed(() => ({
    root: {
        class: [
            'group border border-gray-100 shadow-sm overflow-hidden h-full flex flex-col',
            props.explainable
                ? 'cursor-pointer transition hover:border-[#ff7020]/40 hover:shadow-md'
                : '',
        ],
    },
    body: { class: '!p-0 flex flex-col flex-1' },
    content: {
        class: props.compact ? '!p-4 flex flex-col flex-1 gap-2' : '!p-5 flex flex-col flex-1 gap-3',
    },
}));

function onExplain() {
    if (props.explainable) emit('explain');
}
</script>

<template>
    <Card
        :pt="cardPt"
        role="button"
        @click="onExplain"
    >
        <template #content>
            <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                    <p
                        v-if="theme"
                        class="text-[10px] font-semibold uppercase tracking-wider text-[#ff7020]"
                    >
                        {{ theme }}
                    </p>
                    <h3
                        class="font-semibold leading-tight text-gray-900"
                        :class="compact ? 'text-xs' : 'text-sm'"
                    >
                        {{ title }}
                    </h3>
                </div>
                <div class="flex shrink-0 items-center gap-1.5">
                    <Tag
                        :value="statusLabel"
                        :severity="statusSeverity"
                        class="!text-[10px]"
                    />
                    <i
                        v-if="explainable"
                        class="pi pi-info-circle text-xs text-gray-300 transition-colors group-hover:text-[#ff7020]"
                        aria-hidden="true"
                    />
                </div>
            </div>

            <div v-if="value" class="min-h-[3rem]">
                <p
                    class="font-bold tracking-tight text-gray-900"
                    :class="compact ? 'text-xl' : 'text-3xl'"
                >
                    {{ value }}
                </p>
                <p
                    v-if="delta"
                    class="mt-1 text-sm font-medium"
                    :class="
                        deltaPositive ? 'text-emerald-600' : 'text-red-600'
                    "
                >
                    {{ delta }}
                </p>
                <p
                    v-if="note"
                    class="mt-0.5 text-xs leading-snug text-gray-500"
                >
                    {{ note }}
                </p>
            </div>
            <div
                v-else
                class="flex min-h-[3rem] flex-col justify-center rounded-md border border-dashed border-gray-200 bg-gray-50/80 px-3 py-2"
            >
                <p class="text-sm font-medium text-gray-500">
                    Geen meetwaarde
                </p>
                <p v-if="note" class="mt-0.5 text-xs leading-snug text-gray-500">
                    {{ note }}
                </p>
            </div>

            <p
                v-if="strategicLink"
                class="text-xs text-gray-500"
            >
                <span class="font-medium text-gray-600">Strategisch:</span>
                {{ strategicLink }}
            </p>

            <p
                v-if="footer"
                class="mt-auto border-t border-gray-100 pt-2 text-xs text-gray-500"
            >
                {{ footer }}
            </p>
        </template>
    </Card>
</template>
