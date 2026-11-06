<script setup>
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputNumber from 'primevue/inputnumber';
import Textarea from 'primevue/textarea';
import { computed, ref, watch } from 'vue';

/** @typedef {'enps' | 'ab_players' | 'ebitda'} HandmatigKpiCode */
import { usePage } from '@inertiajs/vue3';

const props = defineProps({
    visible: { type: Boolean, default: false },
    /** Initial tab: enps | ab_players */
    kpiCode: { type: String, default: 'enps' },
});

const emit = defineEmits(['update:visible', 'saved']);

const page = usePage();
const userName = computed(() => page.props.auth?.user?.name ?? 'Onbekend');

const activeKpi = ref('enps');
const year = ref(new Date().getFullYear());
const quarter = ref(Math.ceil((new Date().getMonth() + 1) / 3));
const waarde = ref(null);
const nRespondents = ref(1);
const opmerking = ref('');
const saving = ref(false);
const formError = ref(null);
const success = ref(null);

const kpiTabs = [
    { code: 'ebitda', label: 'EBITDA' },
    { code: 'ab_players', label: 'A/B Players' },
    { code: 'enps', label: 'eNPS' },
];

const isEbitda = computed(() => activeKpi.value === 'ebitda');

watch(
    () => props.visible,
    (open) => {
        if (open) {
            if (props.kpiCode === 'ab_players') {
                activeKpi.value = 'ab_players';
            } else if (props.kpiCode === 'ebitda') {
                activeKpi.value = 'ebitda';
            } else {
                activeKpi.value = 'enps';
            }
            formError.value = null;
            success.value = null;
            waarde.value = null;
            nRespondents.value = 1;
            opmerking.value = '';
        }
    },
);

function periodeEinde() {
    const q = quarter.value;
    const y = year.value;
    const month = q * 3;

    return `${y}-${String(month).padStart(2, '0')}-${new Date(y, month, 0).getDate()}`;
}

async function save() {
    formError.value = null;
    success.value = null;

    if (waarde.value == null || Number.isNaN(Number(waarde.value))) {
        formError.value = 'Vul een waarde in.';

        return;
    }
    if ((nRespondents.value ?? 0) < 1) {
        formError.value = 'Aantal respondenten minimaal 1.';

        return;
    }

    saving.value = true;
    try {
        const csrf =
            document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ?? '';
        const res = await fetch(route('kpi.invoer.handmatig'), {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': csrf,
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                kpi_code: activeKpi.value,
                scope_code: 'concern',
                periode_einde: periodeEinde(),
                waarde: Number(waarde.value),
                n: isEbitda.value ? 1 : Number(nRespondents.value),
                ingevoerd_door: userName.value,
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
            'Opgeslagen. Zichtbaar op de tegel na de volgende Peliqan-sync (tot ca. 1 uur).';
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
        header="Handmatige invoer"
        class="w-full max-w-lg"
        @update:visible="emit('update:visible', $event)"
    >
        <p class="mb-4 text-sm text-gray-600">
            Scope concern. EBITDA = kwartaalcijfer AWC+AFC+ACC (niet cumulatief). Geen
            SAR-jaarcijfers 2019–2025.
        </p>

        <div class="mb-4 flex flex-wrap gap-2">
            <Button
                v-for="tab in kpiTabs"
                :key="tab.code"
                :label="tab.label"
                size="small"
                :severity="activeKpi === tab.code ? 'contrast' : 'secondary'"
                @click="activeKpi = tab.code"
            />
        </div>

        <div class="mb-3 grid grid-cols-2 gap-3">
            <div>
                <label class="mb-1 block text-xs font-semibold uppercase text-gray-500">
                    Jaar
                </label>
                <InputNumber v-model="year" :use-grouping="false" class="w-full" />
            </div>
            <div>
                <label class="mb-1 block text-xs font-semibold uppercase text-gray-500">
                    Kwartaal
                </label>
                <div class="flex gap-1">
                    <Button
                        v-for="q in 4"
                        :key="q"
                        :label="`Q${q}`"
                        size="small"
                        :outlined="quarter !== q"
                        @click="quarter = q"
                    />
                </div>
            </div>
        </div>

        <label class="mb-1 block text-xs font-semibold uppercase text-gray-500">
            {{ isEbitda ? 'EBITDA over dit kwartaal (€)' : 'Waarde' }}
        </label>
        <InputNumber v-model="waarde" class="mb-3 w-full" />

        <template v-if="!isEbitda">
            <label class="mb-1 block text-xs font-semibold uppercase text-gray-500">
                Aantal respondenten / beoordeelden (n)
            </label>
            <InputNumber v-model="nRespondents" :min="1" class="mb-3 w-full" />
        </template>

        <label class="mb-1 block text-xs font-semibold uppercase text-gray-500">
            Toelichting (optioneel)
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
