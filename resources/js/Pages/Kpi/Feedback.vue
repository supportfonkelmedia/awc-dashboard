<script setup>
/**
 * Feedbackoverzicht: alleen voor KPI_FEEDBACK_ADMINS. Status per melding
 * (nieuw / in behandeling / afgerond) wordt direct opgeslagen.
 */
import { KPI_SCREEN_META } from '@/constants/kpiScreens';
import { scopeLabel } from '@/constants/kpiEntiteiten';
import KpiStandaloneLayout from '@/Layouts/KpiStandaloneLayout.vue';
import { Head, Link } from '@inertiajs/vue3';
import { computed, ref } from 'vue';

const props = defineProps({
    items: { type: Array, default: () => [] },
    statuses: { type: Array, default: () => ['nieuw', 'in_behandeling', 'afgerond'] },
});

const STATUS_LABEL = {
    nieuw: 'Nieuw',
    in_behandeling: 'In behandeling',
    afgerond: 'Afgerond',
};
const TYPE_CHIP = {
    fout: { label: 'Fout', cls: 'bg-red-50 text-red-700' },
    verbetering: { label: 'Verbetering', cls: 'bg-awc-blue/10 text-gray-900' },
    vraag: { label: 'Vraag', cls: 'bg-amber-50 text-amber-800' },
};

const rows = ref(props.items.map((i) => ({ ...i, saving: false, error: null })));
const filter = ref('open');

const FILTERS = computed(() => [
    { value: 'open', label: 'Open', count: rows.value.filter((r) => r.status !== 'afgerond').length },
    ...props.statuses.map((s) => ({
        value: s,
        label: STATUS_LABEL[s] ?? s,
        count: rows.value.filter((r) => r.status === s).length,
    })),
    { value: 'all', label: 'Alles', count: rows.value.length },
]);

const zichtbaar = computed(() =>
    rows.value.filter((r) => {
        if (filter.value === 'all') {
            return true;
        }
        if (filter.value === 'open') {
            return r.status !== 'afgerond';
        }

        return r.status === filter.value;
    }),
);

const datumFmt = new Intl.DateTimeFormat('nl-NL', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
});

function datum(iso) {
    return iso ? datumFmt.format(new Date(iso)) : '';
}

function context(row) {
    const delen = [KPI_SCREEN_META[row.scherm]?.title ?? row.scherm];
    if (row.entiteit) {
        delen.push(scopeLabel(row.entiteit));
    }
    if (row.tegel_titel) {
        delen.push(row.tegel_titel);
    }

    return delen.join(' · ');
}

async function zetStatus(row, status) {
    const vorige = row.status;
    row.status = status;
    row.saving = true;
    row.error = null;
    try {
        const csrf =
            document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ?? '';
        const res = await fetch(route('kpi.feedback.update', row.id), {
            method: 'PATCH',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': csrf,
            },
            credentials: 'same-origin',
            body: JSON.stringify({ status }),
        });
        if (!res.ok) {
            throw new Error(`Status opslaan mislukt (${res.status})`);
        }
    } catch (e) {
        row.status = vorige;
        row.error = e?.message ?? 'Status opslaan mislukt';
    } finally {
        row.saving = false;
    }
}
</script>

<template>
    <Head title="Feedback" />

    <KpiStandaloneLayout>
        <header class="bg-awc-black text-white">
            <div
                class="mx-auto flex max-w-[1440px] items-center justify-between gap-3 px-4 py-3 lg:px-8"
            >
                <div class="min-w-0">
                    <p class="truncate text-sm font-semibold text-white">
                        Amsterdam Warehouse Company
                    </p>
                    <p class="text-xs text-white/60">MT-dashboard</p>
                </div>
                <Link
                    :href="route('kpi.screen', { scherm: 'strategisch' })"
                    class="inline-flex items-center gap-1 text-xs text-white/80 hover:text-white"
                >
                    <i class="pi pi-angle-left text-[11px]" aria-hidden="true" />
                    Terug naar het dashboard
                </Link>
            </div>
        </header>

        <main class="mx-auto max-w-[1440px] px-4 py-6 lg:px-8">
            <h1 class="text-xl font-semibold text-gray-900">Feedback</h1>
            <p class="mt-1 max-w-3xl text-xs text-gray-600">
                Meldingen uit de feedbackknop. Zet een melding op ‘In behandeling’ zodra je
                ermee bezig bent en op ‘Afgerond’ als het is opgelost of beantwoord.
            </p>

            <div
                role="group"
                aria-label="Filter op status"
                class="mt-5 flex flex-wrap gap-2"
            >
                <button
                    v-for="f in FILTERS"
                    :key="f.value"
                    type="button"
                    :aria-pressed="filter === f.value"
                    class="rounded-full border px-3 py-1 text-xs transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-awc-orange"
                    :class="
                        filter === f.value
                            ? 'border-awc-orange bg-awc-orange font-semibold text-white'
                            : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                    "
                    @click="filter = f.value"
                >
                    {{ f.label }} <span class="tabular-nums opacity-80">{{ f.count }}</span>
                </button>
            </div>

            <p
                v-if="!zichtbaar.length"
                class="mt-8 rounded-xl border border-dashed border-gray-300 bg-white px-4 py-10 text-center text-sm text-gray-500"
            >
                {{
                    rows.length
                        ? 'Geen meldingen met deze status.'
                        : 'Nog geen feedback ontvangen. Meldingen verschijnen hier zodra iemand de feedbackknop gebruikt.'
                }}
            </p>

            <ul v-else class="mt-5 space-y-3">
                <li
                    v-for="row in zichtbaar"
                    :key="row.id"
                    class="rounded-xl border border-gray-200 bg-white p-4"
                >
                    <div class="flex flex-wrap items-start justify-between gap-3">
                        <div class="min-w-0 flex-1">
                            <div class="flex flex-wrap items-center gap-2">
                                <span
                                    class="rounded px-1.5 py-0.5 text-[10px] font-semibold"
                                    :class="TYPE_CHIP[row.type]?.cls ?? 'bg-gray-100 text-gray-700'"
                                >
                                    {{ TYPE_CHIP[row.type]?.label ?? row.type }}
                                </span>
                                <a
                                    v-if="row.url"
                                    :href="row.url"
                                    class="truncate text-xs text-gray-600 underline-offset-2 hover:text-gray-900 hover:underline"
                                >
                                    {{ context(row) }}
                                </a>
                                <span v-else class="truncate text-xs text-gray-600">
                                    {{ context(row) }}
                                </span>
                            </div>
                            <p class="mt-2 whitespace-pre-line text-sm text-gray-900">
                                {{ row.bericht }}
                            </p>
                            <p class="mt-2 text-[11px] text-gray-500">
                                {{ row.ingediend_door }} · {{ datum(row.ingediend_op) }}
                            </p>
                        </div>

                        <div class="flex shrink-0 flex-col items-end gap-2">
                            <label class="flex items-center gap-2 text-xs text-gray-500">
                                <span class="sr-only">Status van melding {{ row.id }}</span>
                                <select
                                    :value="row.status"
                                    :disabled="row.saving"
                                    class="rounded border border-gray-300 bg-white py-1 pl-2 pr-8 text-sm text-gray-800 focus:border-awc-orange focus:outline-none focus:ring-1 focus:ring-awc-orange"
                                    @change="zetStatus(row, $event.target.value)"
                                >
                                    <option v-for="s in statuses" :key="s" :value="s">
                                        {{ STATUS_LABEL[s] ?? s }}
                                    </option>
                                </select>
                            </label>
                            <p v-if="row.error" class="text-xs text-red-600" role="alert">
                                {{ row.error }}
                            </p>
                            <a
                                v-if="row.screenshot_url"
                                :href="row.screenshot_url"
                                target="_blank"
                                rel="noopener"
                                class="block"
                            >
                                <img
                                    :src="row.screenshot_url"
                                    :alt="`Screenshot bij melding ${row.id}`"
                                    loading="lazy"
                                    class="h-20 w-32 rounded border border-gray-200 object-cover object-top"
                                />
                            </a>
                        </div>
                    </div>
                </li>
            </ul>
        </main>
    </KpiStandaloneLayout>
</template>
