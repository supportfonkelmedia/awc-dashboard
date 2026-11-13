<script setup>
import { computed } from 'vue';
import AfcInfo from '@/Components/Kpi/KpiInfo.vue';
import AfcKaart from './AfcKaart.vue';
import AfcTabel from './AfcTabel.vue';
import { MAANDEN_KORT, aansluiting, ketenPerJaar } from '@/utils/afcAnalyse';
import { euro, euroKort, getal, procent } from '@/utils/afcFormat';

const props = defineProps({
    zendingRows: { type: Array, required: true },
    resultaatRows: { type: Array, required: true },
    jaar: { type: Number, required: true },
});

const maanden = computed(() => aansluiting(props.zendingRows, props.resultaatRows, props.jaar));
const totaal = (veld) => maanden.value.reduce((s, r) => s + r[veld], 0);

const kolommen = [
    { key: 'maand', label: 'Maand', fmt: (v) => MAANDEN_KORT[v - 1] },
    { key: 'omzetSprinter', label: 'Omzet Sprinter (incl. invoerrechten)', fmt: euro, rechts: true },
    { key: 'omzetCash', label: 'Omzet Cash', fmt: euro, rechts: true },
    { key: 'margeSprinter', label: 'Marge Sprinter', fmt: euro, rechts: true },
    { key: 'margeCash', label: 'Marge Cash', fmt: euro, rechts: true },
    { key: 'kostprijsCash', label: 'Kostprijs Cash', fmt: euro, rechts: true },
    { key: 'invoerrechten', label: 'Invoerrechten doorbelast', fmt: euro, rechts: true },
    { key: 'simCargo', label: 'Sim Cargo (6021)', fmt: euro, rechts: true },
];

const keten = computed(() => ketenPerJaar(props.resultaatRows));
const ketenKolommen = [
    { key: 'jaar', label: 'Jaar' },
    { key: 'simCargo', label: 'Sim Cargo netto (6021)', fmt: euro, rechts: true },
    { key: 'svz', label: 'SVZ (6010, 6050)', fmt: euro, rechts: true },
    { key: 'samen', label: 'Samen', fmt: euro, rechts: true },
    { key: 'kostprijs', label: 'Totale kostprijs (6xxx)', fmt: euro, rechts: true },
    { key: 'aandeel', label: 'Aandeel keten in kostprijs', fmt: procent, rechts: true },
    { key: 'maanden', label: 'Maanden', fmt: getal, rechts: true },
];
</script>

<template>
    <details class="group rounded-xl border border-gray-200 bg-white p-5 lg:p-6">
        <summary class="cursor-pointer list-none text-base font-semibold text-gray-900">
            <span class="mr-1 inline-block transition group-open:rotate-90">›</span>
            Financiële aansluiting en ketenkosten
        </summary>

        <h3 class="mt-5 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
            Sprinter tegen Cash, per maand van {{ jaar }}
            <AfcInfo
                :tekst="[
                    'Sprinter telt op rapportagedatum, Cash op grootboekperiode (zoals de MT-tegels); per maand lopen ze uiteen. Over een heel jaar hoort de brutomarge dicht bij elkaar te liggen.',
                    'Het omzetverschil komt deels doordat Cash invoerrechten niet als omzet boekt. Alle richtingen.',
                ]"
            />
        </h3>
        <div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
            <AfcKaart label="Brutomarge Sprinter, heel jaar" :waarde="euroKort(totaal('margeSprinter'))" />
            <AfcKaart label="Brutomarge Cash (8xxx min 6xxx)" :waarde="euroKort(totaal('margeCash'))" />
            <AfcKaart
                label="Omzet Sprinter min Cash"
                :waarde="euroKort(totaal('omzetSprinter') - totaal('omzetCash'))"
                :sub="`waarvan invoerrechten ${euroKort(totaal('invoerrechten'))}`"
            />
        </div>
        <AfcTabel class="mt-4" :kolommen="kolommen" :rijen="maanden" />

        <h3 class="mt-8 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
            Sim Cargo (ILN) en SVZ in Cash
            <AfcInfo
                :tekst="[
                    'Sim Cargo komt rechtstreeks vanuit de bank op 6021: het netto clearingbedrag op betaaldatum. Facturen, creditnota\'s (AFC als depot 216) en vaste maandlasten zitten in één bedrag.',
                    'SVZ (voorhalen en uitrijden) staat als inkoopfactuur op 6010 en 6050.',
                ]"
            />
        </h3>
        <AfcTabel class="mt-3" :kolommen="ketenKolommen" :rijen="keten" />
    </details>
</template>
