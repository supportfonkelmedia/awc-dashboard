<script setup>
import { computed, ref, watch } from 'vue';
import AfcBlok from './AfcBlok.vue';
import AfcGrafiek from './AfcGrafiek.vue';
import AfcKeuze from './AfcKeuze.vue';
import AfcTabel from './AfcTabel.vue';
import { MAANDEN_KORT, cumulatiefPerJaar, resultaatPerJaar } from '@/utils/afcAnalyse';
import { euro, groeiKlasse, groeiTekst, procent } from '@/utils/afcFormat';

const props = defineProps({
    rows: { type: Array, required: true },
    lopendJaar: { type: Number, required: true },
    laatsteVolleMaand: { type: Number, required: true },
});

const tmMaand = ref(props.laatsteVolleMaand || 12);
// Ander jaar gekozen: terug naar de laatste volle maand van dat jaar.
watch(
    () => [props.lopendJaar, props.laatsteVolleMaand],
    () => {
        tmMaand.value = props.laatsteVolleMaand || 12;
    },
);
const toon = ref('resultaat_voor_belasting');

const maandOpties = computed(() =>
    MAANDEN_KORT.map((m, i) => ({
        value: i + 1,
        label: i + 1 === props.laatsteVolleMaand ? `${m} (laatste volle maand)` : m,
    })),
);

const perJaar = computed(() => resultaatPerJaar(props.rows, tmMaand.value));

const kolommen = [
    { key: 'jaar', label: 'Jaar' },
    { key: 'omzet', label: 'Omzet (8xxx)', fmt: euro, rechts: true },
    { key: 'kostprijs', label: 'Kostprijs (6xxx)', fmt: euro, rechts: true },
    { key: 'brutomarge', label: 'Brutomarge', fmt: euro, rechts: true },
    { key: 'brutomargePct', label: 'Brutomarge %', fmt: procent, rechts: true },
    { key: 'bedrijfskosten', label: 'Bedrijfskosten (4xxx)', fmt: euro, rechts: true },
    { key: 'overig', label: 'Overig (9000)', fmt: euro, rechts: true },
    { key: 'resultaat', label: 'Resultaat vóór belasting', fmt: euro, rechts: true },
    { key: 'groeiOmzet', label: 'Groei omzet', fmt: groeiTekst, rechts: true, klasse: (r) => groeiKlasse(r.groeiOmzet) },
    { key: 'resultaatVerschil', label: 'Resultaat t.o.v. vorig jaar', fmt: (v) => (v == null ? '' : (v > 0 ? '+' : '') + euro(v)), rechts: true, klasse: (r) => groeiKlasse(r.resultaatVerschil) },
];

const toonOpties = [
    { value: 'resultaat_voor_belasting', label: 'Resultaat vóór belasting' },
    { value: 'omzet', label: 'Omzet' },
    { value: 'brutomarge', label: 'Brutomarge' },
];

const jaarKleuren = ['#A3A3A3', '#000000', '#0496FF', '#FF6700'];
const reeksen = computed(() =>
    cumulatiefPerJaar(props.rows, toon.value, props.lopendJaar, tmMaand.value).map((r, i, alle) => ({
        label: String(r.jaar),
        data: r.data,
        kleur: jaarKleuren[(jaarKleuren.length - alle.length + i) % jaarKleuren.length],
    })),
);
</script>

<template>
    <AfcBlok
        :titel="`Resultaat volgens Cash t/m ${MAANDEN_KORT[tmMaand - 1]}, per jaar`"
        :uitleg="[
            'Grootboek in Cash, op boekperiode (boekjaar leidend). Vennootschapsbelasting (9100) en de afsluitboeking (9993) tellen niet mee.',
            'Niet afgesloten maanden missen vaak nog kosten; jaarafsluiting landt in december.',
            'Het richtingfilter geldt hier niet: Cash kent geen richting.',
        ]"
    >
        <template #acties>
            <AfcKeuze v-model="tmMaand" label="T/m maand" :opties="maandOpties" />
        </template>

        <AfcTabel :kolommen="kolommen" :rijen="perJaar" />

        <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <h3 class="text-sm font-semibold text-gray-900">Cumulatief per maand, jaren naast elkaar</h3>
            <AfcKeuze v-model="toon" label="Toon" :opties="toonOpties" />
        </div>
        <AfcGrafiek class="mt-3" :labels="MAANDEN_KORT" :reeksen="reeksen" />
    </AfcBlok>
</template>
