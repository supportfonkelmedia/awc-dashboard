<script setup>
import { Link, usePage } from '@inertiajs/vue3';
import { computed } from 'vue';

defineProps({
    scherm: {
        type: String,
        required: true,
    },
    bijgewerktLabel: {
        type: String,
        default: 'onbekend',
    },
    controles: {
        type: Object,
        default: () => ({ fout: 0, let_op: 0, ok: 0 }),
    },
    stale: { type: Boolean, default: false },
    fixture: { type: Boolean, default: false },
});

const page = usePage();
const isFeedbackAdmin = computed(() => Boolean(page.props.auth?.isFeedbackAdmin));

const tactischControlesUrl = `${route('kpi.screen', { scherm: 'tactisch' })}#datakwaliteit`;
</script>

<template>
    <header class="bg-awc-black text-white">
        <div
            class="mx-auto flex max-w-[1440px] flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between lg:px-8"
        >
            <div class="flex min-w-0 items-center gap-3">
                <!-- Hier komt het AWC-logo (SVG uit de Figma-stijlgids); geen nagetekend icoon. -->
                <div class="min-w-0">
                    <p
                        class="truncate text-sm font-semibold text-white"
                    >
                        Amsterdam Warehouse Company
                    </p>
                    <p class="text-xs text-white/60">MT-dashboard</p>
                </div>
            </div>

            <div
                class="flex flex-wrap items-center gap-3 text-sm sm:justify-end"
            >
                <span
                    v-if="fixture"
                    class="rounded-full bg-amber-500/20 px-2 py-0.5 text-[11px] font-medium text-amber-200 ring-1 ring-amber-400/40"
                    title="Acceptatie-fixture; geen live Peliqan-data"
                >
                    Demo-data
                </span>
                <span
                    v-if="stale"
                    class="rounded-full bg-awc-orange/100/20 px-2 py-0.5 text-[11px] font-medium text-orange-200 ring-1 ring-orange-400/40"
                    title="Gecachte data; Peliqan niet bereikbaar"
                >
                    Cache
                </span>
                <span class="text-white/70">
                    Bijgewerkt:
                    <span class="font-medium text-white">{{ bijgewerktLabel }}</span>
                </span>
                <Link
                    :href="tactischControlesUrl"
                    class="flex flex-wrap items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs ring-1 ring-white/10 transition hover:bg-white/20"
                >
                    <span class="text-white/80">Datacontroles</span>
                    <span class="text-red-400">{{ controles.fout }} fout</span>
                    <span class="text-amber-400">{{ controles.let_op }} let op</span>
                    <span class="text-emerald-400">{{ controles.ok }} ok</span>
                </Link>
                <Link
                    v-if="isFeedbackAdmin"
                    :href="route('kpi.feedback.index')"
                    class="text-xs text-white/70 underline-offset-2 hover:text-white hover:underline"
                >
                    Feedbackoverzicht
                </Link>
            </div>
        </div>
    </header>
</template>
