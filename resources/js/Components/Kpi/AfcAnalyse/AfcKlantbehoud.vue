<script setup>
import { computed, ref } from 'vue';
import AfcBlok from './AfcBlok.vue';
import AfcKeuze from './AfcKeuze.vue';
import AfcTabel from './AfcTabel.vue';
import { KLANTSTATUSSEN, klantenMetStatus, statusOverzicht } from '@/utils/afcAnalyse';
import { datumKort, euro, getal, procent } from '@/utils/afcFormat';

const props = defineProps({
    klanten: { type: Array, required: true },
    retentie: { type: Array, required: true },
});

const overzicht = computed(() => statusOverzicht(props.klanten));
const overzichtKolommen = [
    { key: 'status', label: 'Status nu' },
    { key: 'klanten', label: 'Klanten', fmt: getal, rechts: true },
    { key: 'omzetVorig12m', label: 'Omzet 12 tot 24 mnd geleden', fmt: euro, rechts: true },
    { key: 'omzet12m', label: 'Omzet afgelopen 12 mnd', fmt: euro, rechts: true },
];

const perJaar = computed(() => [...props.retentie].sort((a, b) => Number(a.jaar) - Number(b.jaar)));
const jaarKolommen = [
    { key: 'jaar', label: 'Jaar', fmt: (v, r) => (r.lopend_jaar === true || r.lopend_jaar === 'true' ? `${v} (lopend)` : v) },
    { key: 'actieve_klanten', label: 'Actieve klanten', fmt: getal, rechts: true },
    { key: 'behouden', label: 'Behouden', fmt: getal, rechts: true },
    { key: 'weggevallen', label: 'Weggevallen', fmt: getal, rechts: true },
    { key: 'nieuw', label: 'Nieuw', fmt: getal, rechts: true },
    { key: 'teruggekeerd', label: 'Teruggekeerd', fmt: getal, rechts: true },
    { key: 'met_1_zending', label: 'Met 1 zending dat jaar', fmt: getal, rechts: true },
    { key: 'retentie_pct', label: 'Retentie', fmt: procent, rechts: true },
    { key: 'churn_pct', label: 'Churn', fmt: procent, rechts: true },
    { key: 'omzet_weggevallen_vorig_jaar', label: 'Omzet weggevallen klanten (jaar ervoor)', fmt: euro, rechts: true },
    { key: 'omzet_nieuwe_klanten', label: 'Omzet nieuwe klanten', fmt: euro, rechts: true },
];

const status = ref('Verloren');
const statusOpties = KLANTSTATUSSEN.map((s) => ({ value: s, label: s }));
const lijst = computed(() => klantenMetStatus(props.klanten, status.value));
const lijstKolommen = [
    { key: 'klant', label: 'Klant', fmt: (v, r) => (r.debiteurnummer ? `${v} (${r.debiteurnummer})` : v) },
    { key: 'eerste_zending', label: 'Eerste zending', fmt: datumKort },
    { key: 'laatste_zending', label: 'Laatste zending', fmt: datumKort },
    { key: 'dagen_sinds_laatste_zending', label: 'Dagen geleden', fmt: getal, rechts: true },
    { key: 'zendingen_totaal', label: 'Zendingen totaal', fmt: getal, rechts: true },
    { key: 'omzet_vorige_12m', label: 'Omzet 12 tot 24 mnd geleden', fmt: euro, rechts: true },
    { key: 'omzet_12m', label: 'Omzet afgelopen 12 mnd', fmt: euro, rechts: true },
    { key: 'modaliteiten_12m', label: 'Modaliteiten' },
    { key: 'eigenaren_12m', label: 'Dossiereigenaren' },
];
</script>

<template>
    <AfcBlok
        titel="Klantbehoud en churn"
        intro="Per klant (opdrachtgever in Sprinter) over alle zendingen sinds maart 2023, op aanmaakdatum. Verloren = laatste zending meer dan 90 dagen geleden (Eenmalig als het bij één zending bleef). Nieuw = eerste zending in de afgelopen 365 dagen. Dalend = omzet afgelopen 12 maanden minder dan 75% van de 12 maanden daarvoor. Het richtingfilter geldt hier niet."
    >
        <AfcTabel :kolommen="overzichtKolommen" :rijen="overzicht" />

        <h3 class="mt-6 text-sm font-semibold text-gray-900">Per kalenderjaar, ten opzichte van het jaar ervoor</h3>
        <AfcTabel class="mt-2" :kolommen="jaarKolommen" :rijen="perJaar" />
        <p class="mt-2 max-w-3xl text-xs leading-relaxed text-gray-500">
            Het lopende jaar is nog niet compleet: klanten die dit jaar nog niet, maar vorig jaar wel verscheepten, tellen hier als weggevallen. 2024 is afgezet tegen 2023, waarvan de gegevens pas in maart beginnen.
        </p>

        <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <h3 class="text-sm font-semibold text-gray-900">Klanten per status</h3>
            <AfcKeuze v-model="status" label="Status" :opties="statusOpties" />
        </div>
        <AfcTabel class="mt-2" :kolommen="lijstKolommen" :rijen="lijst" sorteerbaar />
        <p class="mt-2 text-xs text-gray-500">
            Maximaal 50 klanten, gesorteerd op omzet (bij Verloren, Dalend en Eenmalig op de omzet 12 tot 24 maanden geleden).
        </p>
    </AfcBlok>
</template>
