<script setup>
import { computed, ref } from 'vue';
import AfcBlok from './AfcBlok.vue';
import AfcInfo from '@/Components/Kpi/KpiInfo.vue';
import AfcKeuze from './AfcKeuze.vue';
import AfcTabel from './AfcTabel.vue';
import Chart from 'primevue/chart';
import { KLANTSTATUSSEN, klantenMetStatus, omzetInUit, statusOverzicht } from '@/utils/afcAnalyse';
import { KLEUR, euroAs, tickStijl, waardeLabels } from '@/utils/afcChart';
import { datumKort, euro, euroKort, getal, groeiKlasse, procent } from '@/utils/afcFormat';

const props = defineProps({
    klanten: { type: Array, required: true },
    retentie: { type: Array, required: true },
    geldtNiet: { type: String, default: null },
});

const num = (v) => (v == null || v === '' ? 0 : Number(v));

const overzicht = computed(() => statusOverzicht(props.klanten));
const overzichtKolommen = [
    { key: 'status', label: 'Status nu' },
    { key: 'klanten', label: 'Klanten', fmt: getal, rechts: true },
    { key: 'omzetVorig12m', label: 'Omzet 12 tot 24 mnd geleden', fmt: euroKort, rechts: true },
    { key: 'omzet12m', label: 'Omzet afgelopen 12 mnd', fmt: euroKort, rechts: true },
];

const perJaar = computed(() =>
    [...props.retentie]
        .sort((a, b) => Number(a.jaar) - Number(b.jaar))
        .map((r) => ({
            ...r,
            // Eerste jaar zonder jaar ervoor: iedereen is 'nieuw', een saldo zegt dan niets.
            netto_omzet:
                num(r.actief_vorig_jaar) > 0
                    ? num(r.omzet_nieuwe_klanten) - num(r.omzet_weggevallen_vorig_jaar)
                    : null,
        })),
);
const jaarKolommen = [
    { key: 'jaar', label: 'Jaar', fmt: (v, r) => (r.lopend_jaar === true || r.lopend_jaar === 'true' ? `${v} (lopend)` : v) },
    { key: 'actieve_klanten', label: 'Actieve klanten', fmt: getal, rechts: true },
    { key: 'nieuw', label: 'Nieuw', fmt: getal, rechts: true },
    { key: 'weggevallen', label: 'Weggevallen', fmt: getal, rechts: true },
    { key: 'retentie_pct', label: 'Retentie', fmt: procent, rechts: true },
    {
        key: 'netto_omzet',
        label: 'Omzet nieuw min weggevallen',
        fmt: (v) => (v == null ? '' : (v > 0 ? '+' : '') + euroKort(v)),
        rechts: true,
        klasse: (r) => groeiKlasse(r.netto_omzet),
    },
];

const inUit = computed(() => omzetInUit(props.retentie));
const plus = (v) => (v > 0 ? '+' : v < 0 ? '−' : '±') + euroKort(Math.abs(v));

const inUitData = computed(() => ({
    labels: inUit.value.map((r) => (r.lopend ? `${r.jaar} (lopend)` : String(r.jaar))),
    datasets: [
        {
            label: 'Nieuwe klanten',
            data: inUit.value.map((r) => r.nieuw),
            backgroundColor: inUit.value.map((r) => (r.lopend ? 'rgba(4, 150, 255, 0.5)' : KLEUR.blauw)),
            borderRadius: 2,
            maxBarThickness: 40,
            stack: 'a',
            waardeLabel: (i) => euroKort(inUit.value[i].nieuw),
        },
        {
            label: 'Weggevallen klanten',
            data: inUit.value.map((r) => -r.weg),
            backgroundColor: inUit.value.map((r) => (r.lopend ? 'rgba(255, 103, 0, 0.5)' : KLEUR.oranje)),
            borderRadius: 2,
            maxBarThickness: 40,
            stack: 'a',
            waardeLabel: (i) => `−${euroKort(inUit.value[i].weg)}`,
            labelOnder: () => true,
        },
        {
            type: 'line',
            label: 'Netto',
            data: inUit.value.map((r) => r.netto),
            showLine: false,
            pointStyle: 'rectRot',
            pointRadius: 6,
            pointHoverRadius: 7,
            pointBackgroundColor: KLEUR.zwart,
            pointBorderColor: '#fff',
            pointBorderWidth: 1.5,
            // Eigen stapel en bovenop tekenen: het saldo valt vaak binnen een staaf.
            stack: 'saldo',
            order: -1,
        },
    ],
}));

const inUitOptions = computed(() => ({
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 18, bottom: 4 } },
    interaction: { mode: 'index', intersect: false },
    plugins: {
        legend: { display: false },
        tooltip: {
            callbacks: {
                label: (ctx) => {
                    const r = inUit.value[ctx.dataIndex];
                    if (ctx.datasetIndex === 0) {
                        return `Nieuw: ${euro(r.nieuw)} (${getal(r.klantenNieuw)} klanten)`;
                    }
                    if (ctx.datasetIndex === 1) {
                        return `Weggevallen: ${euro(r.weg)} (${getal(r.klantenWeg)} klanten)`;
                    }

                    return `Netto: ${(r.netto > 0 ? '+' : '') + euro(r.netto)}`;
                },
            },
        },
    },
    scales: {
        x: { stacked: true, grid: { display: false }, ticks: { ...tickStijl, maxRotation: 0 } },
        y: {
            stacked: true,
            grace: '12%',
            grid: { color: (ctx) => (ctx.tick.value === 0 ? '#A3A3A3' : KLEUR.raster) },
            border: { display: false },
            ticks: { ...tickStijl, maxTicksLimit: 6, callback: euroAs },
        },
    },
}));

const inUitLezing = computed(() => {
    const af = inUit.value.filter((r) => !r.lopend);
    const laatste = af[af.length - 1];
    if (!laatste) {
        return null;
    }
    const vorige = af[af.length - 2];
    let zin = `In ${laatste.jaar} brachten nieuwe klanten ${euroKort(laatste.nieuw)} en viel ${euroKort(laatste.weg)} weg: netto ${plus(laatste.netto)}`;
    if (vorige) {
        zin += ` (${vorige.jaar}: ${plus(vorige.netto)})`;
    }

    return `${zin}.`;
});

const status = ref('Verloren');
const statusOpties = KLANTSTATUSSEN.map((s) => ({ value: s, label: s }));
const lijst = computed(() => klantenMetStatus(props.klanten, status.value));
const lijstKolommen = [
    { key: 'klant', label: 'Klant', fmt: (v, r) => (r.debiteurnummer ? `${v} (${r.debiteurnummer})` : v) },
    { key: 'eerste_zending', label: 'Eerste zending', fmt: datumKort },
    { key: 'laatste_zending', label: 'Laatste zending', fmt: datumKort },
    { key: 'dagen_sinds_laatste_zending', label: 'Dagen geleden', fmt: getal, rechts: true },
    { key: 'zendingen_totaal', label: 'Zendingen totaal', fmt: getal, rechts: true },
    { key: 'omzet_vorige_12m', label: 'Omzet 12 tot 24 mnd geleden', fmt: euroKort, rechts: true },
    { key: 'omzet_12m', label: 'Omzet afgelopen 12 mnd', fmt: euroKort, rechts: true },
    { key: 'modaliteiten_12m', label: 'Modaliteiten' },
    { key: 'eigenaren_12m', label: 'Dossiereigenaren' },
];
</script>

<template>
    <AfcBlok
        titel="Klantbehoud en churn"
        :geldt-niet="geldtNiet"
        :uitleg="[
            'Per opdrachtgever in Sprinter, alle zendingen sinds maart 2023, op aanmaakdatum.',
            'Verloren: laatste zending meer dan 90 dagen geleden (Eenmalig bij één zending). Nieuw: eerste zending in de afgelopen 365 dagen. Dalend: omzet afgelopen 12 maanden onder 75% van de 12 maanden daarvoor.',
            'Richting en modaliteit gelden hier niet.',
            'Retentie: deel van de klanten van vorig jaar dat dit jaar weer verscheept. Churn is 100% min retentie.',
        ]"
    >
        <h3 class="flex items-center gap-1.5 text-sm font-semibold text-gray-900">
            Omzet erbij en eraf door klanten die komen en gaan
            <AfcInfo tekst="Blauw: omzet van klanten die dat jaar voor het eerst verscheepten. Oranje: omzet die het jaar ervoor kwam van klanten die dit jaar niet meer verschepen. Het ruitje is het saldo. Het lopende jaar is lichter: wie nog gaat verschepen, telt nu als weggevallen." />
        </h3>
        <p v-if="inUitLezing" class="mt-1 text-sm text-gray-700">{{ inUitLezing }}</p>
        <div v-if="inUit.length" class="mt-3 h-60">
            <Chart type="bar" :data="inUitData" :options="inUitOptions" :plugins="[waardeLabels]" class="h-full w-full" />
        </div>
        <ul v-if="inUit.length" class="mt-2 flex flex-wrap gap-4 text-xs text-gray-600">
            <li class="flex items-center gap-1.5"><span class="inline-block h-2.5 w-2.5 rounded-sm bg-awc-blue" />nieuwe klanten</li>
            <li class="flex items-center gap-1.5"><span class="inline-block h-2.5 w-2.5 rounded-sm bg-awc-orange" />weggevallen klanten</li>
            <li class="flex items-center gap-1.5"><span class="inline-block h-2 w-2 rotate-45 bg-black" />saldo</li>
        </ul>

        <h3 class="mt-6 text-sm font-semibold text-gray-900">Status nu</h3>
        <AfcTabel class="mt-2" :kolommen="overzichtKolommen" :rijen="overzicht" />

        <h3 class="mt-6 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
            Per kalenderjaar, ten opzichte van het jaar ervoor
            <AfcInfo tekst="Het lopende jaar is nog niet compleet: wie dit jaar nog niet maar vorig jaar wel verscheepte, telt als weggevallen. 2023 begint pas in maart. De laatste kolom: omzet van nieuwe klanten min de omzet die weggevallen klanten het jaar ervoor brachten." />
        </h3>
        <AfcTabel class="mt-2" :kolommen="jaarKolommen" :rijen="perJaar" />

        <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <h3 class="flex items-center gap-1.5 text-sm font-semibold text-gray-900">
                Klanten per status
                <AfcInfo tekst="Maximaal 50 klanten, op omzet. Bij Verloren, Dalend en Eenmalig op de omzet van 12 tot 24 maanden geleden." />
            </h3>
            <AfcKeuze v-model="status" label="Status" :opties="statusOpties" />
        </div>
        <AfcTabel class="mt-2" :kolommen="lijstKolommen" :rijen="lijst" sorteerbaar :beperk="10" />
    </AfcBlok>
</template>
