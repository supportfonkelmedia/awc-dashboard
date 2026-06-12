<script setup>
import { STATUS_LABELS, STATUS_TAG_SEVERITY } from '@/config/mtKpiFramework';
import Drawer from 'primevue/drawer';
import Tag from 'primevue/tag';
import { computed } from 'vue';

const visible = defineModel('visible', { type: Boolean, default: false });

const props = defineProps({
    kpi: {
        type: Object,
        default: null,
    },
});

const statusLabel = computed(
    () => STATUS_LABELS[props.kpi?.status] ?? props.kpi?.status ?? '',
);

const statusSeverity = computed(
    () => STATUS_TAG_SEVERITY[props.kpi?.status] ?? 'secondary',
);

const statusHint = computed(() => {
    switch (props.kpi?.status) {
        case 'live':
            return 'Live — wordt actief gemeten uit de bron.';
        case 'in_development':
            return 'In ontwikkeling — toont een proxy of voorlopige waarde; definitie wordt nog aangescherpt.';
        case 'not_measured':
            return 'Niet gemeten — de benodigde brondata ontbreekt of is nog niet gekoppeld.';
        case 'to_define':
            return 'Te definiëren — de meetdefinitie moet nog worden vastgelegd.';
        default:
            return '';
    }
});
</script>

<template>
    <Drawer
        v-model:visible="visible"
        position="right"
        class="kpi-explain-drawer !w-[min(34rem,95vw)]"
        :pt="{
            root: { class: '!shadow-2xl' },
            header: { class: '!border-b !border-gray-100 !pb-4' },
            content: { class: '!pt-4' },
        }"
    >
        <template #header>
            <div class="min-w-0 pr-2">
                <p
                    v-if="kpi?.theme"
                    class="text-xs font-semibold uppercase tracking-wider text-[#ff7020]"
                >
                    {{ kpi.theme }}
                </p>
                <h2 class="mt-1 text-lg font-bold text-gray-900">
                    {{ kpi?.title ?? 'KPI' }}
                </h2>
                <Tag
                    v-if="kpi"
                    :value="statusLabel"
                    :severity="statusSeverity"
                    class="mt-2 !text-[10px]"
                />
            </div>
        </template>

        <div
            v-if="kpi"
            class="flex flex-col gap-5"
        >
            <div
                v-if="kpi.value"
                class="flex flex-wrap items-baseline gap-x-4 gap-y-1 rounded-lg border border-gray-100 bg-gray-50 px-4 py-3"
            >
                <span class="text-2xl font-bold text-gray-900">{{
                    kpi.value
                }}</span>
                <span
                    v-if="kpi.delta"
                    class="text-sm font-medium"
                    :class="
                        kpi.deltaPositive
                            ? 'text-emerald-600'
                            : 'text-red-600'
                    "
                >
                    {{ kpi.delta }}
                </span>
            </div>

            <section v-if="kpi.description">
                <h3
                    class="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400"
                >
                    Wat meet deze KPI?
                </h3>
                <p class="text-sm leading-relaxed text-gray-700">
                    {{ kpi.description }}
                </p>
            </section>

            <section v-if="kpi.method">
                <h3
                    class="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400"
                >
                    Hoe wordt het berekend?
                </h3>
                <p class="text-sm leading-relaxed text-gray-700">
                    {{ kpi.method }}
                </p>
            </section>

            <section v-if="kpi.note">
                <h3
                    class="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400"
                >
                    Opmerking
                </h3>
                <p class="text-sm leading-relaxed text-gray-700">
                    {{ kpi.note }}
                </p>
            </section>

            <section v-if="statusHint">
                <h3
                    class="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400"
                >
                    Status
                </h3>
                <p class="text-sm leading-relaxed text-gray-700">
                    {{ statusHint }}
                </p>
            </section>

            <dl
                class="grid grid-cols-1 gap-3 rounded-lg border border-gray-100 bg-gray-50/60 px-4 py-3 text-sm"
            >
                <div v-if="kpi.source" class="flex justify-between gap-4">
                    <dt class="font-medium text-gray-500">Bron</dt>
                    <dd class="text-right text-gray-800">{{ kpi.source }}</dd>
                </div>
                <div
                    v-if="kpi.strategicLink"
                    class="flex justify-between gap-4"
                >
                    <dt class="font-medium text-gray-500">Strategische KPI</dt>
                    <dd class="text-right text-gray-800">
                        {{ kpi.strategicLink }}
                    </dd>
                </div>
            </dl>
        </div>
    </Drawer>
</template>
