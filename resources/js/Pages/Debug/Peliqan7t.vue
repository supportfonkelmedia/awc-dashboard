<script setup>
import ManagementLayout from '@/Layouts/ManagementLayout.vue';
import { Head } from '@inertiajs/vue3';
import { computed, ref } from 'vue';

const props = defineProps({
    config: { type: Object, required: true },
});

const loading = ref(false);
const error = ref(null);
const result = ref(null);
const elapsedMs = ref(null);
const lastLookback = ref(null);

const lookbackOptions = [180, 365, 730, 1825, 3650];

const configReady = computed(
    () => props.config?.jwt_set && props.config?.url_set,
);

async function call(lookback) {
    if (loading.value) return;
    loading.value = true;
    error.value = null;
    result.value = null;
    elapsedMs.value = null;
    lastLookback.value = lookback;

    const params = new URLSearchParams();
    if (lookback === 'sample') params.set('sample', '1');
    else if (lookback) params.set('lookback', String(lookback));

    try {
        const res = await fetch(`${route('debug.peliqan.7t.call')}?${params}`, {
            headers: {
                Accept: 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        });
        const json = await res.json();

        if (!res.ok || json.ok === false) {
            error.value = json.error || `HTTP ${res.status}`;
            result.value = json.payload ?? json;
            return;
        }

        elapsedMs.value = json.elapsed_ms ?? null;
        result.value = json.payload ?? json;
    } catch (e) {
        error.value = e?.message ?? 'Request mislukt';
    } finally {
        loading.value = false;
    }
}

const data = computed(() => result.value?.data ?? null);
const summary = computed(() => {
    const d = data.value;
    if (!d || d.sample) return null;
    return [
        { label: 'Admin ID', value: d.admin_id ?? '—' },
        { label: 'Lookback (dgn)', value: d.lookback_days ?? '—' },
        {
            label: 'Occupancy',
            value:
                d.occupancy?.rate != null
                    ? `${d.occupancy.rate}% (${d.occupancy.occupied}/${d.occupancy.total})`
                    : '—',
        },
        {
            label: 'Storage lead time',
            value: d.storage_lead_time_days ?? '—',
        },
        {
            label: 'Inventory accuracy',
            value:
                d.inventory_accuracy_pct != null
                    ? `${d.inventory_accuracy_pct}%`
                    : '—',
        },
        { label: 'Ontvangsten', value: d.ontvangsten_count ?? '—' },
    ];
});

const pretty = computed(() =>
    result.value ? JSON.stringify(result.value, null, 2) : '',
);
</script>

<template>
    <Head title="7T Debug" />

    <ManagementLayout>
        <div class="mx-auto max-w-[1100px] px-4 py-6 lg:px-6">
            <div class="mb-6">
                <h1 class="text-2xl font-bold tracking-tight text-gray-900">
                    7T WMS — Debug
                </h1>
                <p class="mt-1 text-sm text-gray-500">
                    Roept de directe 7T endpoint aan (geen cache). Probeer een
                    groter lookback-venster om te zien wanneer er data verschijnt.
                    <span v-if="config.url_host">
                        Host:
                        <code class="rounded bg-gray-100 px-1">{{
                            config.url_host
                        }}</code>
                    </span>
                </p>
            </div>

            <div
                v-if="!configReady"
                class="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900"
            >
                <p class="font-semibold">Niet geconfigureerd</p>
                <p class="mt-1">
                    Zet <code>PELIQAN_JWT</code> en
                    <code>PELIQAN_AWC_7T_URL</code> in <code>.env</code>.
                </p>
            </div>

            <div class="mb-4 flex flex-wrap items-center gap-2">
                <span class="mr-1 text-sm font-medium text-gray-600">
                    Lookback:
                </span>
                <button
                    v-for="n in lookbackOptions"
                    :key="n"
                    type="button"
                    class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gray-800 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                    :class="{
                        'border-black bg-black text-white hover:bg-gray-800':
                            lastLookback === n,
                    }"
                    :disabled="loading || !configReady"
                    @click="call(n)"
                >
                    {{ n }} dgn
                </button>
                <button
                    type="button"
                    class="ml-2 rounded-lg border border-indigo-300 bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-800 transition hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-50"
                    :class="{
                        'border-indigo-700 bg-indigo-700 text-white hover:bg-indigo-800':
                            lastLookback === 'sample',
                    }"
                    :disabled="loading || !configReady"
                    @click="call('sample')"
                >
                    Sample tabellen
                </button>
            </div>

            <div class="mb-6 flex items-center gap-3">
                <span v-if="loading" class="text-sm text-gray-500">
                    Bezig… (7T is traag, ~25s)
                </span>
                <span
                    v-else-if="elapsedMs != null"
                    class="text-sm text-gray-500"
                >
                    Klaar in {{ (elapsedMs / 1000).toFixed(1) }}s
                </span>
            </div>

            <div
                v-if="error"
                class="mb-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-800"
            >
                <p class="font-semibold">Fout</p>
                <p class="mt-1 break-words">{{ error }}</p>
            </div>

            <div
                v-if="summary"
                class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6"
            >
                <div
                    v-for="s in summary"
                    :key="s.label"
                    class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
                >
                    <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">
                        {{ s.label }}
                    </p>
                    <p class="mt-1 text-lg font-bold text-gray-900">
                        {{ s.value }}
                    </p>
                </div>
            </div>

            <div
                v-if="pretty"
                class="rounded-xl border border-gray-200 bg-gray-950 p-4 shadow-sm"
            >
                <pre
                    class="overflow-x-auto text-xs leading-relaxed text-gray-100"
                ><code>{{ pretty }}</code></pre>
            </div>
        </div>
    </ManagementLayout>
</template>
