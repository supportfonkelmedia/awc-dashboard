<script setup>
/**
 * Zwevende feedbackknop rechtsonder (MT 10-11-2026), naar het voorbeeld van Leap.
 *
 * De knop blijft staan terwijl de kaart erboven open is, zodat hij kan zeggen
 * wat hij opent (aria-expanded/aria-controls). Escape of een klik buiten de
 * kaart sluit hem; Escape zet de focus terug op de knop.
 *
 * Context gaat automatisch mee: scherm, gekozen entiteit en, als de melding via
 * het icoon op een tegel kwam, die tegel. Het tegelicoon opent de kaart via
 * `openSignal` (een teller, zodat twee keer vragen ook twee keer opent).
 *
 * Screenshot: plakken (Cmd/Ctrl+V) waar de cursor ook staat, slepen op de
 * kaart of klikken om te kiezen. Eén afbeelding, max. 5 MB.
 */
import { KPI_SCREEN_META } from '@/constants/kpiScreens';
import { scopeLabel } from '@/constants/kpiEntiteiten';
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';

const props = defineProps({
    scherm: { type: String, required: true },
    /** scope_code van de gekozen entiteit, of 'concern' */
    entiteit: { type: String, default: 'concern' },
    /** Tegel waar de melding over gaat; null = het scherm als geheel */
    tile: { type: Object, default: null },
    /** Ophogen opent de kaart (tegelicoon) */
    openSignal: { type: Number, default: 0 },
});

const emit = defineEmits(['clear-tile']);

const TYPES = [
    { value: 'fout', label: 'Fout', icon: 'pi-exclamation-triangle' },
    { value: 'verbetering', label: 'Idee', icon: 'pi-lightbulb' },
    { value: 'vraag', label: 'Vraag', icon: 'pi-question-circle' },
];
const MAX_BYTES = 5 * 1024 * 1024;
const CONFIRM_MS = 6000;

const open = ref(false);
const type = ref('fout');
const bericht = ref('');
const bestand = ref(null);
const previewUrl = ref(null);
const saving = ref(false);
const formError = ref(null);
const bevestigd = ref(false);
const dragging = ref(false);
let dragDepth = 0;
let confirmTimer = null;

const rootRef = ref(null);
const triggerRef = ref(null);
const berichtRef = ref(null);
const fileRef = ref(null);

const panelId = 'kpi-feedback-panel';
const titleId = 'kpi-feedback-title';

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

const canSubmit = computed(() => bericht.value.trim().length > 0 && !saving.value);

function zetBestand(file) {
    formError.value = null;
    if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value);
        previewUrl.value = null;
    }
    bestand.value = null;
    if (!file) {
        return;
    }
    if (!file.type.startsWith('image/')) {
        formError.value = 'Alleen afbeeldingen (png, jpg, webp, gif).';

        return;
    }
    if (file.size > MAX_BYTES) {
        formError.value = 'Deze afbeelding is groter dan 5 MB.';

        return;
    }
    bestand.value = file;
    previewUrl.value = URL.createObjectURL(file);
}

function onFileChange(event) {
    zetBestand(event.target.files?.[0] ?? null);
    event.target.value = '';
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

// Slepen op de hele kaart: een bestand dat net naast een kleine dropzone valt,
// laat de browser anders naar het bestand navigeren (en de getypte tekst kwijt).
function draagtBestanden(event) {
    return [...(event.dataTransfer?.types ?? [])].includes('Files');
}
function onDragEnter(event) {
    if (!draagtBestanden(event)) {
        return;
    }
    dragDepth += 1;
    dragging.value = true;
}
function onDragOver(event) {
    if (!draagtBestanden(event)) {
        return;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
}
function onDragLeave() {
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) {
        dragging.value = false;
    }
}
function onDrop(event) {
    if (!draagtBestanden(event)) {
        return;
    }
    event.preventDefault();
    dragDepth = 0;
    dragging.value = false;
    zetBestand(event.dataTransfer.files?.[0] ?? null);
}

function openen() {
    formError.value = null;
    bevestigd.value = false;
    open.value = true;
    nextTick(() => berichtRef.value?.focus());
}

function sluiten(focusTerug) {
    open.value = false;
    formError.value = null;
    emit('clear-tile');
    if (focusTerug) {
        triggerRef.value?.focus();
    }
}

function onDocMouseDown(event) {
    if (rootRef.value && !rootRef.value.contains(event.target)) {
        sluiten(false);
    }
}
function onDocKeydown(event) {
    if (event.key === 'Escape' && !document.querySelector('[aria-modal="true"]')) {
        sluiten(true);
    }
}

watch(open, (isOpen) => {
    if (isOpen) {
        document.addEventListener('mousedown', onDocMouseDown);
        document.addEventListener('keydown', onDocKeydown);
    } else {
        document.removeEventListener('mousedown', onDocMouseDown);
        document.removeEventListener('keydown', onDocKeydown);
    }
});

watch(
    () => props.openSignal,
    (n) => {
        if (n > 0) {
            openen();
        }
    },
);

watch(bevestigd, (v) => {
    window.clearTimeout(confirmTimer);
    if (v) {
        confirmTimer = window.setTimeout(() => {
            bevestigd.value = false;
        }, CONFIRM_MS);
    }
});

onBeforeUnmount(() => {
    document.removeEventListener('mousedown', onDocMouseDown);
    document.removeEventListener('keydown', onDocKeydown);
    window.clearTimeout(confirmTimer);
    if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value);
    }
});

async function verstuur() {
    if (!canSubmit.value) {
        return;
    }
    formError.value = null;

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
            formError.value = eersteFout ?? json.message ?? 'Versturen is niet gelukt.';

            return;
        }
        bericht.value = '';
        type.value = 'fout';
        zetBestand(null);
        sluiten(true);
        bevestigd.value = true;
    } catch (e) {
        formError.value = `Versturen is niet gelukt. ${e?.message ?? ''}`.trim();
    } finally {
        saving.value = false;
    }
}
</script>

<template>
    <div
        ref="rootRef"
        class="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-2"
    >
        <section
            v-if="open"
            :id="panelId"
            role="dialog"
            :aria-labelledby="titleId"
            class="w-80 max-w-[calc(100vw-2.5rem)] rounded-xl border border-gray-200 bg-white p-4 shadow-xl"
            @paste="onPaste"
            @dragenter="onDragEnter"
            @dragover="onDragOver"
            @dragleave="onDragLeave"
            @drop="onDrop"
        >
            <div class="mb-2 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <i class="pi pi-comment text-[13px] text-awc-orange" aria-hidden="true" />
                    <h2 :id="titleId" class="text-xs font-semibold text-gray-900">Feedback</h2>
                </div>
                <button
                    type="button"
                    class="flex h-6 w-6 items-center justify-center rounded text-gray-400 hover:bg-gray-100 hover:text-gray-800"
                    aria-label="Sluiten"
                    @click="sluiten(true)"
                >
                    <i class="pi pi-times text-[11px]" aria-hidden="true" />
                </button>
            </div>

            <p class="mb-3 text-[11px] leading-snug text-gray-500">
                Klopt een cijfer niet, mis je iets of heb je een vraag? Je melding gaat
                rechtstreeks naar het dashboardteam.
            </p>

            <div
                role="radiogroup"
                aria-label="Soort melding"
                class="mb-3 grid grid-cols-3 gap-1.5"
            >
                <button
                    v-for="t in TYPES"
                    :key="t.value"
                    type="button"
                    role="radio"
                    :aria-checked="type === t.value"
                    class="flex flex-col items-center gap-1 rounded-md border px-2 py-2 text-[11px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-awc-orange"
                    :class="
                        type === t.value
                            ? 'border-awc-black bg-awc-black text-white'
                            : 'border-gray-200 bg-white text-gray-700 hover:border-gray-400'
                    "
                    @click="type = t.value"
                >
                    <i :class="['pi', t.icon, 'text-[13px]']" aria-hidden="true" />
                    <span class="font-medium">{{ t.label }}</span>
                </button>
            </div>

            <textarea
                ref="berichtRef"
                v-model="bericht"
                rows="4"
                maxlength="5000"
                aria-label="Je melding"
                placeholder="Wat zie je, of wat zou je willen?"
                :disabled="saving"
                class="mb-2 block w-full resize-none rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-awc-orange focus:outline-none focus:ring-1 focus:ring-awc-orange"
            />

            <div v-if="previewUrl" class="relative mb-2 inline-block">
                <img
                    :src="previewUrl"
                    :alt="bestand?.name ?? 'Screenshot'"
                    class="block h-16 w-24 rounded border border-gray-200 object-cover object-top"
                />
                <button
                    type="button"
                    class="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-500 shadow-sm hover:text-red-600"
                    aria-label="Screenshot weghalen"
                    title="Screenshot weghalen"
                    @click="zetBestand(null)"
                >
                    <i class="pi pi-times text-[9px]" aria-hidden="true" />
                </button>
            </div>

            <input
                ref="fileRef"
                type="file"
                tabindex="-1"
                aria-hidden="true"
                accept="image/png,image/jpeg,image/webp,image/gif"
                class="sr-only"
                @change="onFileChange"
            />
            <button
                v-if="!previewUrl"
                type="button"
                :disabled="saving"
                class="mb-2 flex w-full flex-col items-center gap-0.5 rounded-md border border-dashed px-3 py-3 text-center transition-colors disabled:cursor-not-allowed disabled:opacity-60"
                :class="
                    dragging
                        ? 'border-awc-orange bg-awc-orange/10'
                        : 'border-gray-300 bg-gray-50 hover:border-gray-500'
                "
                @click="fileRef?.click()"
            >
                <span class="flex items-center gap-1.5 text-xs font-medium text-gray-800">
                    <i class="pi pi-image text-[12px]" aria-hidden="true" />
                    {{ dragging ? 'Laat los om toe te voegen' : 'Screenshot toevoegen' }}
                </span>
                <span class="text-[10px] text-gray-500">
                    Sleep, plak (Cmd/Ctrl+V) of klik om te kiezen
                </span>
            </button>

            <div class="flex items-center justify-between gap-2">
                <p class="min-w-0 truncate text-[10px] text-gray-500" :title="contextLabel">
                    Over: {{ contextLabel }}
                </p>
                <button
                    type="button"
                    :disabled="!canSubmit"
                    class="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-awc-orange px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-awc-orange-dark disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-awc-black"
                    @click="verstuur"
                >
                    <i
                        :class="['pi', saving ? 'pi-spinner pi-spin' : 'pi-send', 'text-[11px]']"
                        aria-hidden="true"
                    />
                    {{ saving ? 'Versturen…' : 'Versturen' }}
                </button>
            </div>

            <p
                v-if="formError"
                class="mt-2 rounded-md bg-red-50 px-2.5 py-1.5 text-xs text-red-700"
                role="alert"
            >
                {{ formError }}
            </p>
        </section>

        <div class="flex items-center gap-2">
            <p
                v-if="bevestigd && !open"
                role="status"
                class="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800 shadow-md"
            >
                <span class="font-semibold">Bedankt, verzonden.</span>
                Het dashboardteam pakt het op.
            </p>
            <button
                ref="triggerRef"
                type="button"
                class="inline-flex items-center gap-2 rounded-full bg-awc-black px-4 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-gray-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-awc-orange focus-visible:ring-offset-2"
                aria-label="Feedback geven"
                :aria-expanded="open"
                :aria-controls="open ? panelId : undefined"
                @click="open ? sluiten(true) : openen()"
            >
                <i class="pi pi-comment text-[13px] text-awc-orange" aria-hidden="true" />
                Feedback
            </button>
        </div>
    </div>
</template>
