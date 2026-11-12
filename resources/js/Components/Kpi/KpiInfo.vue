<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue';

/**
 * Info-icoon met uitleg (gedeeld door tegels en de AFC-analyse) bij hover, focus (toetsenbord) en tik (telefoon). Escape of scrollen sluit.
 * De uitleg staat vast in beeld (position: fixed) en wordt binnen het scherm geschoven.
 * `tekst` mag een string of een lijst alinea's zijn.
 */
const props = defineProps({
    tekst: { type: [String, Array], required: true },
    label: { type: String, default: 'Uitleg' },
});

const id = `kpi-info-${Math.random().toString(36).slice(2, 8)}`;
const knop = ref(null);
const uitleg = ref(null);
const open = ref(false);
const vast = ref(false);
const positie = ref({ top: '0px', left: '0px' });

const alineas = computed(() => (Array.isArray(props.tekst) ? props.tekst : [props.tekst]).filter(Boolean));

const BREEDTE = 288;
const MARGE = 12;
let scrollStart = 0;

// Sluit pas bij echt scrollen: focus met het toetsenbord scrolt de knop zelf ook even in beeld.
function opScroll() {
    if (Math.abs(window.scrollY - scrollStart) > 40) {
        sluit();
    }
}

async function toon() {
    const r = knop.value?.getBoundingClientRect();
    if (r) {
        const breedte = Math.min(BREEDTE, window.innerWidth - 2 * MARGE);
        const left = Math.min(Math.max(r.left, MARGE), window.innerWidth - breedte - MARGE);
        positie.value = { top: `${Math.round(r.bottom + 6)}px`, left: `${Math.round(left)}px`, width: `${breedte}px` };
    }
    open.value = true;
    await nextTick();
    // Past de uitleg niet onder het icoon (onderaan het scherm), dan erboven.
    const h = uitleg.value?.offsetHeight ?? 0;
    if (r && r.bottom + 6 + h > window.innerHeight - MARGE && r.top - 6 - h > MARGE) {
        positie.value = { ...positie.value, top: `${Math.round(r.top - 6 - h)}px` };
    }
    scrollStart = window.scrollY;
    window.addEventListener('scroll', opScroll, { passive: true });
}

function verberg() {
    if (!vast.value) {
        open.value = false;
    }
}

function wissel() {
    vast.value = !vast.value;
    if (vast.value) {
        toon();
    } else {
        open.value = false;
    }
}

function sluit() {
    vast.value = false;
    open.value = false;
    window.removeEventListener('scroll', opScroll);
}

onBeforeUnmount(() => window.removeEventListener('scroll', opScroll));
</script>

<template>
    <span class="inline-flex align-middle" @mouseenter="toon" @mouseleave="verberg" @keydown.escape="sluit">
        <button
            ref="knop"
            type="button"
            class="inline-flex h-5 w-5 items-center justify-center rounded-full text-gray-400 transition-colors hover:text-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-awc-orange"
            :aria-label="label"
            :aria-describedby="open ? id : undefined"
            :aria-expanded="open"
            @click="wissel"
            @focus="toon"
            @blur="sluit"
        >
            <i class="pi pi-info-circle text-[13px]" aria-hidden="true" />
        </button>
        <span
            v-show="open"
            ref="uitleg"
            :id="id"
            role="tooltip"
            class="fixed z-50 space-y-1.5 rounded-md bg-awc-black px-3 py-2 text-left text-xs font-normal normal-case leading-relaxed text-white shadow-lg"
            :style="positie"
        >
            <span v-for="(a, i) in alineas" :key="i" class="block">{{ a }}</span>
        </span>
    </span>
</template>
