<script setup>
import { computed } from 'vue';
import AfcBlok from './AfcBlok.vue';
import AfcTabel from './AfcTabel.vue';
import { perEigenaar } from '@/utils/afcAnalyse';
import { euro, getal, procent } from '@/utils/afcFormat';

const props = defineProps({
    rows: { type: Array, required: true },
    jaar: { type: Number, required: true },
    beschikbareJaren: { type: Array, required: true },
});

const rijen = computed(() => perEigenaar(props.rows, props.jaar));
const kolommen = [
    { key: 'eigenaar', label: 'Dossiereigenaar' },
    { key: 'zendingen', label: 'Zendingen', fmt: getal, rechts: true },
    { key: 'omzet', label: 'Omzet', fmt: euro, rechts: true },
    { key: 'marge', label: 'Marge', fmt: euro, rechts: true },
    { key: 'margePct', label: 'Marge %', fmt: procent, rechts: true },
    { key: 'zonderAfdeling', label: 'Zendingen zonder afdeling', fmt: getal, rechts: true },
];
</script>

<template>
    <AfcBlok
        :titel="`Per dossiereigenaar, ${jaar} t/m vandaag`"
        uitleg="Eigenaar van het dossier in Sprinter. De afdeling is daar vaak leeg; de laatste kolom telt die zendingen. Teams volgen later."
    >
        <p v-if="!beschikbareJaren.includes(jaar)" class="text-sm text-gray-500">
            Cijfers per eigenaar zijn er voor {{ beschikbareJaren.join(' en ') }}.
        </p>
        <AfcTabel v-else :kolommen="kolommen" :rijen="rijen" sorteerbaar />
    </AfcBlok>
</template>
