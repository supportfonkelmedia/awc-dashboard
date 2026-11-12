<script setup>
import { computed } from 'vue';
import Message from 'primevue/message';

const props = defineProps({
    payload: {
        type: Object,
        default: null,
    },
});

const ERNST = { fout: 2, let_op: 1 };

// Er zijn meerdere Sprinter-controles (versheid, volume): toon de ernstigste.
const alert = computed(() => {
    const rows = props.payload?.kpi_controles ?? [];
    const sprinter = rows
        .filter((r) => {
            const name = String(r.controle ?? '').toLowerCase();

            return name.includes('sprinter') || String(r.bron ?? '').toLowerCase().includes('sprinter');
        })
        .map((r) => ({ ...r, ernst: ERNST[String(r.status ?? '').toLowerCase()] ?? 0 }))
        .filter((r) => r.ernst > 0)
        .sort((a, b) => b.ernst - a.ernst)[0];

    if (!sprinter) {
        return null;
    }

    const fout = sprinter.ernst === 2;
    const detail = [sprinter.controle, sprinter.toelichting].filter(Boolean).join(': ');

    return {
        severity: fout ? 'error' : 'warn',
        summary: fout
            ? 'Sprinter-cijfers zijn mogelijk onvolledig'
            : 'Let op bij de Sprinter-cijfers',
        detail,
    };
});
</script>

<template>
    <Message
        v-if="alert"
        :severity="alert.severity"
        :closable="false"
        class="mt-6 w-full"
    >
        <span class="font-semibold">{{ alert.summary }}</span>
        <span v-if="alert.detail" class="mt-1 block text-sm opacity-90">
            {{ alert.detail }}
        </span>
    </Message>
</template>
