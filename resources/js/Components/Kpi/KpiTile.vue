<script setup>
import { leesbaar } from '@/utils/leesbaar';
import KpiInfo from '@/Components/Kpi/KpiInfo.vue';
import KpiTileFooter from '@/Components/Kpi/KpiTileFooter.vue';
import KpiTegelGrafiek from '@/Components/Kpi/KpiTegelGrafiek.vue';
import KpiModalSplit from '@/Components/Kpi/KpiModalSplit.vue';
import { computed } from 'vue';

const props = defineProps({
    tile: {
        type: Object,
        required: true,
    },
    /** Rijen uit kpi_afc_sprinter_maand: de Modal split-tegel toont daarmee weg / zee / lucht. */
    modaliteitRows: {
        type: Array,
        default: null,
    },
});

/** Modal split met maanddata: verdeling i.p.v. alleen de lijn van het aandeel weg. */
const toonSplit = computed(
    () => props.tile.kpiCode === 'afc_modal_split' && (props.modaliteitRows?.length ?? 0) > 0,
);

/** Statussen waarvan de reden zichtbaar blijft: er is actie of voorzichtigheid nodig. */
const REDEN_ZICHTBAAR = new Set(['onbetrouwbaar', 'wacht_op_invoer', 'data_ontbreekt', 'data_onvolledig']);

const redenZichtbaar = computed(
    () => props.tile.resolved.display !== 'value' && REDEN_ZICHTBAAR.has(props.tile.resolved.state),
);

/** Uitleg achter het info-icoon naast de titel. */
const uitleg = computed(() => {
    const t = props.tile;
    const delen = [];
    if (t.resolved.display === 'value' && t.toelichting) {
        delen.push(t.toelichting);
    }
    if (t.resolved.display !== 'value' && t.resolved.bodyText && !redenZichtbaar.value) {
        delen.push(t.resolved.bodyText);
    }
    return delen;
});

const emit = defineEmits(['details', 'invoer', 'doel', 'feedback']);

const stateBoxClass = {
    data_onvolledig: 'bg-red-50 text-red-700',
    data_ontbreekt: 'bg-red-50 text-red-700',
    in_validatie: 'bg-awc-blue/10 text-gray-900',
    wacht_op_invoer: 'bg-amber-50 text-amber-800',
    onbetrouwbaar: 'bg-red-50 text-red-700',
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
                <h3 class="flex items-center gap-1 text-[13px] font-semibold leading-snug text-gray-900">
                    {{ tile.titel }}
                    <KpiInfo v-if="uitleg.length" :tekst="uitleg" :label="`Uitleg bij ${tile.titel}`" />
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
                    <p class="text-[28px] font-semibold leading-none tracking-tight text-gray-900">
                        {{ tile.valueNumber ?? tile.valueFormatted }}
                    </p>
                    <span v-if="tile.valueUnit" class="text-[11px] text-gray-500">
                        {{ tile.valueUnit }}{{ toonSplit ? ' over de weg' : '' }}
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
                    v-if="tile.resolved.bodyText && redenZichtbaar"
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

            <!-- Bekende kanttekening bij de data (kpi_betrouwbaarheid, niveau let_op). -->
            <p
                v-if="tile.betrouwbaarheid === 'let_op' && tile.betrouwbaarheidReden"
                class="mt-2 inline-flex items-center gap-1 self-start rounded-full bg-amber-50 py-0.5 pl-2 pr-1 text-[11px] font-semibold text-amber-800 ring-1 ring-amber-200"
            >
                <i class="pi pi-exclamation-triangle text-[10px]" aria-hidden="true" />
                Let op
                <KpiInfo :tekst="tile.betrouwbaarheidReden" :label="`Let op bij ${tile.titel}`" />
            </p>

            <!-- Een onbetrouwbaar cijfer krijgt ook geen trendlijn: de historie heeft hetzelfde probleem. -->
            <div v-if="tile.resolved.state === 'onbetrouwbaar'" class="mt-auto" />
            <KpiModalSplit
                v-else-if="toonSplit"
                :rows="modaliteitRows"
                :stand-per="tile.oordeelRow?.stand_per ? String(tile.oordeelRow.stand_per) : null"
                class="mt-auto pt-4"
            />
            <KpiTegelGrafiek
                v-else
                :series="tile.trendSeriesAll ?? tile.trendSeries"
                :periode="tile.trendPeriode ?? 'all'"
                :kpi-code="tile.kpiCode"
                :eenheid="tile.oordeelRow?.eenheid ?? 'ratio'"
                :richting="tile.richting"
                :doel="tile.doel"
                :empty-text="
                    tile.trendFilteredOut
                        ? `Geen punten in ${tile.trendPeriode}`
                        : 'Nog geen maandhistorie'
                "
                height-class="h-20"
                class="mt-auto pt-4"
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
