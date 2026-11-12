<script setup>
/**
 * Feedbackformulier (MT 10-11-2026): fout, verbetering of vraag, optioneel met
 * screenshot (uploaden of plakken). Scherm, entiteit en tegel gaan automatisch mee.
 */
import { KPI_SCREEN_META } from '@/constants/kpiScreens';
import { scopeLabel } from '@/constants/kpiEntiteiten';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import Textarea from 'primevue/textarea';
import { computed, onBeforeUnmount, ref, watch } from 'vue';

const props = defineProps({
    visible: { type: Boolean, default: false },
    scherm: { type: String, required: true },
    /** scope_code van de gekozen entiteit, of 'concern' */
    entiteit: { type: String, default: 'concern' },
    /** Tegel waar de melding over gaat; null = het scherm als geheel */
    tile: { type: Object, default: null },
});

const emit = defineEmits(['update:visible']);

const TYPES = [
    { value: 'fout', label: 'Fout' },
    { value: 'verbetering', label: 'Verbetering' },
    { value: 'vraag', label: 'Vraag' },
];
const MAX_BYTES = 5 * 1024 * 1024;

const type = ref('fout');
const bericht = ref('');
const bestand = ref(null);
const previewUrl = ref(null);
const fileInput = ref(null);
const saving = ref(false);
const formError = ref(null);
const verzonden = ref(false);

const contextLabel = computed(() => {
    const delen = [KPI_SCREEN_META[props.scherm]?.title ?? props.scherm];
    if (props.entiteit && props.entiteit !== 'concern') {
        delen.push(scopeLabel(props.entiteit));
    }
    if (props.tile?.titel) {
        delen.push(props.tile.titel);
    }

    return delen.join(' · ');
});

function zetBestand(file) {
    formError.value = null;
    if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value);
        previewUrl.value = null;
    }
    if (!file) {
        bestand.value = null;

        return;
    }
    if (!file.type.startsWith('image/')) {
        formError.value = 'Alleen afbeeldingen (png, jpg, webp, gif).';

        return;
    }
    if (file.size > MAX_BYTES) {
        formError.value = 'Screenshot is groter dan 5 MB.';

        return;
    }
    bestand.value = file;
    previewUrl.value = URL.createObjectURL(file);
}

function onFileChange(event) {
    zetBestand(event.target.files?.[0] ?? null);
}

function onPaste(event) {
    const item = [...(event.clipboardData?.items ?? [])].find((i) =>
        i.type.startsWith('image/'),
    );
    if (item) {
        event.preventDefault();
        zetBestand(item.getAsFile());
    }
}

function verwijderScreenshot() {
    zetBestand(null);
    if (fileInput.value) {
        fileInput.value.value = '';
    }
}

watch(
    () => props.visible,
    (open) => {
        if (open) {
            type.value = 'fout';
            bericht.value = '';
            verwijderScreenshot();
            formError.value = null;
            verzonden.value = false;
        }
    },
);

onBeforeUnmount(() => {
    if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value);
    }
});

async function verstuur() {
    formError.value = null;
    if (!bericht.value.trim()) {
        formError.value = 'Beschrijf kort wat je ziet of wilt.';

        return;
    }

    const data = new FormData();
    data.append('type', type.value);
    data.append('bericht', bericht.value.trim());
    data.append('scherm', props.scherm);
    if (props.entiteit && props.entiteit !== 'concern') {
        data.append('entiteit', props.entiteit);
    }
    if (props.tile?.kpiCode) {
        data.append('kpi_code', props.tile.kpiCode);
    }
    if (props.tile?.titel) {
        data.append('tegel_titel', props.tile.titel);
    }
    data.append('url', window.location.pathname + window.location.search);
    if (bestand.value) {
        data.append('screenshot', bestand.value);
    }

    saving.value = true;
    try {
        const csrf =
            document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ?? '';
        const res = await fetch(route('kpi.feedback.store'), {
            method: 'POST',
            headers: { Accept: 'application/json', 'X-CSRF-TOKEN': csrf },
            credentials: 'same-origin',
            body: data,
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) {
            const eersteFout = json.errors ? Object.values(json.errors)[0]?.[0] : null;
            formError.value = eersteFout ?? json.message ?? 'Versturen mislukt.';

            return;
        }
        verzonden.value = true;
    } catch (e) {
        formError.value = e?.message ?? 'Versturen mislukt.';
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
        header="Feedback geven"
        class="w-full max-w-lg"
        @update:visible="emit('update:visible', $event)"
    >
        <template v-if="verzonden">
            <p class="text-sm text-gray-800">
                Bedankt, je feedback is ontvangen. Het dashboardteam pakt het op.
            </p>
        </template>

        <form v-else id="kpi-feedback-form" @submit.prevent="verstuur" @paste="onPaste">
            <p class="mb-4 text-xs text-gray-500">
                Over: <span class="font-medium text-gray-700">{{ contextLabel }}</span>
            </p>

            <p
                id="kpi-feedback-type-label"
                class="mb-1 block text-xs font-semibold uppercase text-gray-500"
            >
                Soort
            </p>
            <div
                role="group"
                aria-labelledby="kpi-feedback-type-label"
                class="mb-4 inline-flex overflow-hidden rounded border border-gray-300"
            >
                <button
                    v-for="(t, i) in TYPES"
                    :key="t.value"
                    type="button"
                    :aria-pressed="type === t.value"
                    class="px-3 py-1.5 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#ff7020]"
                    :class="[
                        i > 0 ? 'border-l border-gray-300' : '',
                        type === t.value
                            ? 'bg-[#ff7020] font-semibold text-white'
                            : 'bg-white text-gray-700 hover:bg-gray-50',
                    ]"
                    @click="type = t.value"
                >
                    {{ t.label }}
                </button>
            </div>

            <label
                for="kpi-feedback-bericht"
                class="mb-1 block text-xs font-semibold uppercase text-gray-500"
            >
                Wat zie je of wil je?
            </label>
            <Textarea
                id="kpi-feedback-bericht"
                v-model="bericht"
                rows="4"
                maxlength="5000"
                class="mb-4 w-full"
            />

            <p class="mb-1 block text-xs font-semibold uppercase text-gray-500">
                Screenshot (optioneel)
            </p>
            <div v-if="previewUrl" class="mb-2">
                <img
                    :src="previewUrl"
                    alt="Voorbeeld van je screenshot"
                    class="max-h-48 rounded border border-gray-200"
                />
                <button
                    type="button"
                    class="mt-1 text-xs text-gray-600 underline hover:text-gray-900"
                    @click="verwijderScreenshot"
                >
                    Screenshot weghalen
                </button>
            </div>
            <template v-else>
                <input
                    id="kpi-feedback-screenshot"
                    ref="fileInput"
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    class="block w-full text-sm text-gray-700 file:mr-3 file:rounded file:border file:border-gray-300 file:bg-white file:px-3 file:py-1.5 file:text-sm file:text-gray-800 hover:file:bg-gray-50"
                    aria-label="Screenshot kiezen"
                    @change="onFileChange"
                />
                <p class="mt-1 text-xs text-gray-500">
                    Of plak een screenshot in dit venster (Cmd/Ctrl+V). Max. 5 MB.
                </p>
            </template>

            <p v-if="formError" class="mt-3 text-sm text-red-600" role="alert">
                {{ formError }}
            </p>
        </form>

        <template #footer>
            <template v-if="verzonden">
                <Button label="Sluiten" @click="close" />
            </template>
            <template v-else>
                <Button label="Annuleren" severity="secondary" text @click="close" />
                <Button
                    label="Versturen"
                    type="submit"
                    form="kpi-feedback-form"
                    :loading="saving"
                />
            </template>
        </template>
    </Dialog>
</template>
