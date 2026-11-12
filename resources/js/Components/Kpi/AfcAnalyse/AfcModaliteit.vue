<script setup>
import { computed, ref } from 'vue';
import AfcBlok from './AfcBlok.vue';
import AfcGrafiek from './AfcGrafiek.vue';
import AfcInfo from '@/Components/Kpi/KpiInfo.vue';
import AfcKeuze from './AfcKeuze.vue';
import AfcTabel from './AfcTabel.vue';
import { MAANDEN_KORT, maandModaliteitReeks, perModaliteit } from '@/utils/afcAnalyse';
import { euro, getal, groeiKlasse, groeiTekst, procent } from '@/utils/afcFormat';

const props = defineProps({
    rows: { type: Array, required: true },
    jaar: { type: Number, required: true },
});

const tabel = computed(() => perModaliteit(props.rows, props.jaar));

const kolommen = [
    { key: 'modaliteit', label: 'Modaliteit' },
    { key: 'zendingen', label: 'Zendingen', fmt: getal, rechts: true },
    { key: 'omzet', label: 'Omzet', fmt: euro, rechts: true },
    { key: 'marge', label: 'Marge', fmt: euro, rechts: true },
    { key: 'margePct', label: 'Marge %', fmt: procent, rechts: true },
    { key: 'omzetVorig', label: 'Omzet vorig jaar', fmt: euro, rechts: true },
    { key: 'margeVorig', label: 'Marge vorig jaar', fmt: euro, rechts: true },
    { key: 'margePctVorig', label: 'Marge % vorig jaar', fmt: procent, rechts: true },
    { key: 'groeiOmzet', label: 'Groei omzet', fmt: groeiTekst, rechts: true, klasse: (r) => groeiKlasse(r.groeiOmzet) },
    { key: 'groeiMarge', label: 'Groei marge', fmt: groeiTekst, rechts: true, klasse: (r) => groeiKlasse(r.groeiMarge) },
];

const maat = ref('omzet');
const maatOpties = [
    { value: 'omzet', label: 'Omzet' },
    { value: 'marge', label: 'Marge' },
    { value: 'zendingen', label: 'Zendingen' },
];
const kleuren = { Weg: '#0496FF', Zee: '#000000', Lucht: '#FF6700' };

const reeks = computed(() => maandModaliteitReeks(props.rows, maat.value));
const labels = computed(() =>
    reeks.value.maanden.map((m) => `${MAANDEN_KORT[Number(m.slice(5, 7)) - 1]} ${m.slice(2, 4)}`),
);
const reeksen = computed(() =>
    reeks.value.series.map((s) => ({ label: s.modaliteit, data: s.data, kleur: kleuren[s.modaliteit] })),
);
</script>

<template>
    <AfcBlok
        :titel="`Per modaliteit, ${jaar} t/m vandaag naast dezelfde periode vorig jaar`"
        uitleg="Omzet excl. invoerrechten en btw. Invoerrechten (vooral zee-import) worden zonder marge doorbelast en tellen daarom niet mee."
    >
        <AfcTabel :kolommen="kolommen" :rijen="tabel" :rij-klasse="(r) => (r.isTotaal ? 'afc-totaal' : '')" />

        <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <h3 class="flex items-center gap-1.5 text-sm font-semibold text-gray-900">
                Per maand en modaliteit, sinds januari 2024
                <AfcInfo tekst="Op rapportagedatum in Sprinter. Bij de jaarovergang krijgen openstaande dossiers 1 januari als datum; daarom springt januari omhoog (vooral zee). De lopende maand is nog niet compleet." />
            </h3>
            <AfcKeuze v-model="maat" label="Toon" :opties="maatOpties" />
        </div>
        <AfcGrafiek
            class="mt-3"
            type="bar"
            gestapeld
            :labels="labels"
            :reeksen="reeksen"
            :eenheid="maat === 'zendingen' ? 'aantal' : 'euro'"
        />
    </AfcBlok>
</template>
