<script setup>
import { computed } from 'vue';
import Message from 'primevue/message';

const props = defineProps({
    payload: {
        type: Object,
        default: null,
    },
});

const alert = computed(() => {
    const rows = props.payload?.kpi_controles ?? [];
    const sprinter = rows.find((r) => {
        const name = String(r.controle ?? '').toLowerCase();

        return name.includes('sprinter') || String(r.bron ?? '').toLowerCase().includes('sprinter');
    });

    if (!sprinter) {
        return null;
    }

    const status = String(sprinter.status ?? '').toLowerCase();
    if (status !== 'fout' && status !== 'let_op') {
        return null;
    }

    return {
        severity: status === 'fout' ? 'error' : 'warn',
        summary:
            status === 'fout'
                ? 'Sprinter3000 is sinds augustus onvolledig'
                : 'Sprinter3000 — let op',
        detail: String(sprinter.toelichting ?? sprinter.controle ?? ''),
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
