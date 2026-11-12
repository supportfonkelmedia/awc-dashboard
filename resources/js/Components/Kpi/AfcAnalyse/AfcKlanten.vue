<script setup>
import { computed, ref } from 'vue';
import AfcBlok from './AfcBlok.vue';
import AfcSegment from './AfcSegment.vue';
import AfcTabel from './AfcTabel.vue';
import { topKlanten } from '@/utils/afcAnalyse';
import { euro, getal, procent } from '@/utils/afcFormat';

const props = defineProps({
    rows: { type: Array, required: true },
    jaar: { type: Number, required: true },
    richting: { type: String, required: true },
    beschikbareJaren: { type: Array, required: true },
});

const modaliteit = ref('alle');
const modOpties = [
    { value: 'alle', label: 'Alle' },
    { value: 'Weg', label: 'Weg' },
    { value: 'Zee', label: 'Zee' },
    { value: 'Lucht', label: 'Lucht' },
];

const beschikbaar = computed(() => props.beschikbareJaren.includes(props.jaar));
const top = computed(() =>
    topKlanten(props.rows, props.jaar, { richting: props.richting, modaliteit: modaliteit.value }),
);

const lageMarge = (r) => (r.margePct != null && r.margePct < 10 ? 'font-semibold text-awc-orange' : '');

const kolommen = [
    { key: 'naam', label: 'Klant' },
    { key: 'modaliteiten', label: 'Modaliteiten' },
    { key: 'richtingen', label: 'Richtingen' },
    { key: 'zendingen', label: 'Zendingen', fmt: getal, rechts: true },
    { key: 'omzet', label: 'Omzet', fmt: euro, rechts: true },
    { key: 'marge', label: 'Marge', fmt: euro, rechts: true },
    { key: 'margePct', label: 'Marge %', fmt: procent, rechts: true, klasse: lageMarge },
    { key: 'aandeelMarge', label: 'Aandeel in marge', fmt: procent, rechts: true },
    { key: 'omzetVorig', label: 'Omzet vorig jaar', fmt: euro, rechts: true },
    { key: 'margeVorig', label: 'Marge vorig jaar', fmt: euro, rechts: true },
];
</script>

<template>
    <AfcBlok
        :titel="`Top 40 klanten, ${jaar} t/m vandaag`"
        :uitleg="[
            'Samengevoegd op de vaste debiteur in Cash (tussen haakjes). Betaalt de debiteur voor derden of is er nog nooit gefactureerd, dan staat de klant los als (geen debiteur).',
            'Marge onder 10% is oranje. Klik op een kolomkop om te sorteren.',
        ]"
    >
        <template #acties>
            <AfcSegment v-model="modaliteit" label="Modaliteit" :opties="modOpties" />
        </template>

        <p v-if="!beschikbaar" class="text-sm text-gray-500">
            Klantcijfers zijn er voor {{ beschikbareJaren.join(' en ') }}. Kies een van die jaren.
        </p>
        <AfcTabel v-else :kolommen="kolommen" :rijen="top.rows" sorteerbaar />
    </AfcBlok>
</template>
