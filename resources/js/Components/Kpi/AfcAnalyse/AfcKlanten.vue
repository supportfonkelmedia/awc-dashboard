<script setup>
import { computed } from 'vue';
import AfcBlok from './AfcBlok.vue';
import AfcKlantkaart from './AfcKlantkaart.vue';
import AfcTabel from './AfcTabel.vue';
import { topKlanten } from '@/utils/afcAnalyse';
import { euroKort, getal, procent } from '@/utils/afcFormat';

const props = defineProps({
    rows: { type: Array, required: true },
    jaar: { type: Number, required: true },
    richting: { type: String, required: true },
    modaliteit: { type: String, required: true },
    beschikbareJaren: { type: Array, required: true },
});

const beschikbaar = computed(() => props.beschikbareJaren.includes(props.jaar));
const top = computed(() =>
    topKlanten(props.rows, props.jaar, { richting: props.richting, modaliteit: props.modaliteit }),
);

const lageMarge = (r) => (r.margePct != null && r.margePct < 10 ? 'font-semibold text-awc-orange' : '');

const kolommen = [
    { key: 'naam', label: 'Klant' },
    { key: 'modaliteiten', label: 'Modaliteiten' },
    { key: 'richtingen', label: 'Richtingen' },
    { key: 'zendingen', label: 'Zendingen', fmt: getal, rechts: true },
    { key: 'omzet', label: 'Omzet', fmt: euroKort, rechts: true },
    { key: 'marge', label: 'Marge', fmt: euroKort, rechts: true },
    { key: 'margePct', label: 'Marge %', fmt: procent, rechts: true, klasse: lageMarge },
    { key: 'aandeelMarge', label: 'Aandeel in marge', fmt: procent, rechts: true },
    { key: 'omzetVorig', label: 'Omzet vorig jaar', fmt: euroKort, rechts: true },
    { key: 'margeVorig', label: 'Marge vorig jaar', fmt: euroKort, rechts: true },
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
        <p v-if="!beschikbaar" class="text-sm text-gray-500">
            Klantcijfers zijn er voor {{ beschikbareJaren.join(' en ') }}. Kies een van die jaren.
        </p>
        <template v-else>
            <AfcKlantkaart :klanten="top.rows" />
            <AfcTabel class="mt-6" :kolommen="kolommen" :rijen="top.rows" sorteerbaar :beperk="10" />
        </template>
    </AfcBlok>
</template>
