<script setup>
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputNumber from 'primevue/inputnumber';
import Textarea from 'primevue/textarea';
import { computed, ref, watch } from 'vue';
import { usePage } from '@inertiajs/vue3';

const props = defineProps({
    visible: { type: Boolean, default: false },
    tile: { type: Object, default: null },
});

const emit = defineEmits(['update:visible', 'saved']);

const page = usePage();
const userName = computed(() => page.props.auth?.user?.name ?? 'Onbekend');

const geldigVanafStr = ref('');
const doel = ref(null);
const margeBijna = ref(null);
const opmerking = ref('');
const saving = ref(false);
const formError = ref(null);
const success = ref(null);

watch(
    () => [props.visible, props.tile],
    ([open]) => {
        if (!open || !props.tile) {
            return;
        }
        formError.value = null;
        success.value = null;
        doel.value = props.tile.oordeelRow?.doel ?? null;
        margeBijna.value = null;
        opmerking.value = '';
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        geldigVanafStr.value = `${y}-${m}-01`;
    },
);

const eenheidHint = computed(() => {
    const e = props.tile?.eenheid;
    if (e === 'procent') {
        return 'Procent als 85,0 (niet 0,85).';
    }
    if (e === 'euro') {
        return 'Bedrag in euro (heel getal).';
    }
    if (e === 'ratio') {
        return 'Ratio zoals op de tegel (bijv. 2,40).';
    }

    return 'Zelfde eenheid als de KPI in Peliqan.';
});

function isFirstOfMonth(isoDate) {
    const parts = isoDate.split('-');
    if (parts.length !== 3) {
        return false;
    }

    return parts[2] === '01';
}

async function save() {
    formError.value = null;
    success.value = null;

    if (!props.tile?.kpiCode) {
        formError.value = 'Geen KPI gekoppeld aan deze tegel.';

        return;
    }
    if (doel.value == null || Number.isNaN(Number(doel.value))) {
        formError.value = 'Vul een doel in.';

        return;
    }
    if (!geldigVanafStr.value) {
        formError.value = 'Kies geldig vanaf (1e van de maand).';

        return;
    }
    if (!isFirstOfMonth(geldigVanafStr.value)) {
        formError.value = 'Geldig vanaf moet de 1e van een maand zijn.';

        return;
    }

    saving.value = true;
    try {
        const csrf =
            document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ?? '';
        const res = await fetch(route('kpi.invoer.doelen'), {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': csrf,
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                kpi_code: props.tile.kpiCode,
                scope_code: props.tile.scopeCode || 'concern',
                geldig_vanaf: geldigVanafStr.value,
                doel: Number(doel.value),
                marge_bijna:
                    margeBijna.value != null ? Number(margeBijna.value) : null,
                vastgesteld_door: userName.value,
                opmerking: opmerking.value || null,
            }),
        });
        const json = await res.json();
        if (!res.ok) {
            formError.value =
                json.message ??
                (typeof json.error === 'string' ? json.error : 'Opslaan mislukt');

            return;
        }
        success.value =
            json.message ??
            'Doel opgeslagen. Zichtbaar na Peliqan-sync (tot ca. 1 uur).';
        emit('saved');
    } catch (e) {
        formError.value = e?.message ?? 'Opslaan mislukt';
    } finally {
        saving.value = false;
    }
}

function close() {
    emit('update:visible', false);
}
</script>

<template>
    <Dialog
        :visible="visible"
        modal
        :header="tile ? `Doel voor ${tile.titel}` : 'Doel instellen'"
        class="w-full max-w-lg"
        @update:visible="emit('update:visible', $event)"
    >
        <p v-if="tile" class="mb-2 text-sm text-gray-600">
            {{ tile.kpiCode }} · scope {{ tile.scopeCode || 'concern' }}
        </p>
        <p class="mb-4 text-xs text-gray-500">{{ eenheidHint }}</p>

        <label class="mb-1 block text-sm font-medium text-gray-700">
            Geldig vanaf (1e van de maand)
        </label>
        <input
            v-model="geldigVanafStr"
            type="date"
            class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm"
        />

        <label class="mb-1 block text-sm font-medium text-gray-700">
            Doel
        </label>
        <InputNumber v-model="doel" class="mb-3 w-full" />

        <label class="mb-1 block text-sm font-medium text-gray-700">
            Marge „bijna” (optioneel)
        </label>
        <InputNumber v-model="margeBijna" class="mb-3 w-full" />

        <label class="mb-1 block text-sm font-medium text-gray-700">
            Opmerking (optioneel)
        </label>
        <Textarea v-model="opmerking" rows="2" class="mb-3 w-full" />

        <p v-if="formError" class="mb-2 text-sm text-red-600">{{ formError }}</p>
        <p v-if="success" class="mb-2 text-sm text-emerald-700">{{ success }}</p>

        <template #footer>
            <Button label="Annuleren" severity="secondary" text @click="close" />
            <Button label="Opslaan" :loading="saving" @click="save" />
        </template>
    </Dialog>
</template>
