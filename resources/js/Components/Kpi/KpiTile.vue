<script setup>
import { leesbaar } from '@/utils/leesbaar';
import KpiTileFooter from '@/Components/Kpi/KpiTileFooter.vue';
import KpiTrendSparkline from '@/Components/Kpi/KpiTrendSparkline.vue';

defineProps({
    tile: {
        type: Object,
        required: true,
    },
});

const emit = defineEmits(['details', 'invoer', 'doel', 'feedback']);

const stateBoxClass = {
    data_onvolledig: 'bg-red-50 text-red-700',
    data_ontbreekt: 'bg-red-50 text-red-700',
    in_validatie: 'bg-sky-50 text-sky-800',
    wacht_op_invoer: 'bg-amber-50 text-amber-800',
};

function boxClass(state) {
    return stateBoxClass[state] ?? 'bg-gray-100 text-gray-800';
}

function deltaClass(tone) {
    if (tone === 'good') {
        return 'text-emerald-600';
    }
    if (tone === 'bad') {
        return 'text-red-600';
    }

    return 'text-gray-500';
}

const goalChip = {
    op_doel: { label: 'Op doel', cls: 'bg-emerald-50 text-emerald-700' },
    bijna: { label: 'Bijna op doel', cls: 'bg-amber-50 text-amber-800' },
    onder_doel: { label: 'Onder doel', cls: 'bg-red-50 text-red-700' },
};
</script>

<template>
    <article
        class="flex h-full min-h-[19rem] flex-col rounded-xl border border-gray-200 bg-white"
        :class="tile.element === 'banner' ? 'md:col-span-2' : ''"
    >
        <div class="flex flex-1 flex-col px-4 pt-4">
            <!-- Eyebrow + owner -->
            <div class="flex items-start justify-between gap-2">
                <p class="min-h-[1rem] text-[11px] text-gray-500">
                    {{ leesbaar(tile.themeLabel) }}
                </p>
                <span
                    v-if="tile.eigenaar"
                    class="shrink-0 text-[10px] text-gray-500"
                >
                    {{ tile.eigenaar }}
                </span>
            </div>

            <!-- Title + goal chip -->
            <div class="mt-1 flex items-start justify-between gap-2">
                <h3 class="text-[13px] font-bold leading-snug text-gray-900">
                    {{ tile.titel }}
                </h3>
                <span
                    v-if="tile.goalStatus && goalChip[tile.goalStatus]"
                    :title="tile.goalDoelTekst || undefined"
                    class="shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium"
                    :class="goalChip[tile.goalStatus].cls"
                >
                    {{ goalChip[tile.goalStatus].label }}
                </span>
            </div>
            <p v-if="tile.entiteitNote" class="mt-0.5 text-[11px] text-gray-500">
                {{ tile.entiteitNote }}
            </p>

            <!-- Value state -->
            <template v-if="tile.resolved.display === 'value'">
                <div class="mt-2.5 flex items-baseline gap-1.5">
                    <p class="text-[28px] font-bold leading-none tracking-tight text-gray-900">
                        {{ tile.valueNumber ?? tile.valueFormatted }}
                    </p>
                    <span v-if="tile.valueUnit" class="text-[11px] text-gray-500">
                        {{ tile.valueUnit }}
                    </span>
                </div>

                <div class="mt-2 flex items-center justify-between gap-2">
                    <p
                        v-if="tile.deltaFormatted"
                        class="text-[11px] font-semibold leading-5"
                        :class="deltaClass(tile.deltaTone)"
                    >
                        <span v-if="tile.deltaTone === 'good'">▲</span>
                        <span v-else-if="tile.deltaTone === 'bad'">▼</span>
                        <span v-else>▬</span>
                        {{ tile.deltaFormatted }}
                    </p>
                    <span v-else />
                    <button
                        type="button"
                        class="inline-flex shrink-0 items-center gap-1 rounded-full border border-gray-300 bg-white px-2.5 py-1 text-[10px] font-medium text-gray-700 hover:bg-gray-50"
                        @click="emit('doel', tile)"
                    >
                        <i class="pi pi-bullseye text-[10px]" aria-hidden="true" />
                        Doel instellen
                    </button>
                </div>

                <p v-if="tile.toelichting" class="mt-1.5 text-[11px] leading-snug text-gray-500">
                    {{ tile.toelichting }}
                </p>
            </template>

            <!-- Status state -->
            <template v-else>
                <div
                    class="mt-2.5 rounded-md px-3 py-2 text-xs font-semibold"
                    :class="boxClass(tile.resolved.state)"
                >
                    {{ tile.stateLabel ?? tile.resolved.state }}
                </div>
                <p
                    v-if="tile.resolved.bodyText"
                    class="mt-2 text-[11px] leading-snug text-gray-500"
                >
                    {{ tile.resolved.bodyText }}
                </p>
                <button
                    v-if="tile.resolved.showInvoerKnop"
                    type="button"
                    class="mt-2 inline-flex self-start items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-[11px] font-medium text-gray-800 hover:bg-gray-50"
                    @click="emit('invoer', tile)"
                >
                    Waarde invoeren
                </button>
            </template>

            <KpiTrendSparkline
                :series="tile.trendSeries"
                :eenheid="tile.oordeelRow?.eenheid ?? 'ratio'"
                :empty-text="
                    tile.trendFilteredOut
                        ? `Geen punten in ${tile.trendPeriode}`
                        : 'Nog geen maandhistorie'
                "
                height-class="h-[4.5rem]"
                class="mt-auto pt-5"
            />
        </div>

        <KpiTileFooter
            :tile="tile"
            :show-details="tile.drillViews.length > 0"
            @details="emit('details', tile)"
            @feedback="emit('feedback', tile)"
        />
    </article>
</template>
