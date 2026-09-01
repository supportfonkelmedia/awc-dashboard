import { onMounted, ref, watch } from 'vue';

const BUNDLES = ['cashweb', 'hubspot', 'sprinter'];

const BUNDLE_LABELS = {
    cashweb: 'Cashweb',
    hubspot: 'HubSpot',
    sprinter: 'Sprinter',
};

async function fetchBundle(bundle, filters) {
    const params = new URLSearchParams({
        bundle,
        book_year: filters.book_year,
        month: filters.month,
        quarter: filters.quarter ?? 'all',
        start_date: filters.start_date,
        end_date: filters.end_date,
    });

    const res = await fetch(`${route('mt.peliqan')}?${params}`, {
        headers: {
            Accept: 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    });

    const json = await res.json();

    if (!res.ok) {
        const err = new Error(
            (typeof json.error === 'string' && json.error) ||
                `${BUNDLE_LABELS[bundle]} laden mislukt (HTTP ${res.status})`,
        );
        err.bundle = bundle;
        throw err;
    }

    return { bundle, payload: json };
}

export function useMtPeliqanLoader(filtersRef) {
    const peliqan = ref(null);
    const loading = ref(true);
    const bundleErrors = ref({});

    async function loadPeliqan() {
        loading.value = true;
        bundleErrors.value = {};

        const filters = filtersRef.value;
        if (!filters) {
            loading.value = false;
            return;
        }

        try {
            const results = await Promise.allSettled(
                BUNDLES.map((bundle) => fetchBundle(bundle, filters)),
            );

            const data = {};
            let filtersMeta = null;
            let meta = {};
            const errors = {};
            let anyStale = false;

            for (let i = 0; i < results.length; i++) {
                const bundle = BUNDLES[i];
                const result = results[i];

                if (result.status === 'fulfilled') {
                    const { payload } = result.value;
                    data[bundle] = payload.data ?? null;
                    filtersMeta = filtersMeta ?? payload.filters ?? null;
                    if (payload.meta && typeof payload.meta === 'object') {
                        meta = { ...meta, ...payload.meta };
                    }
                    if (payload.meta?.stale) {
                        anyStale = true;
                    }
                } else {
                    errors[bundle] =
                        result.reason?.message ??
                        `${BUNDLE_LABELS[bundle]} laden mislukt`;
                }
            }

            bundleErrors.value = errors;

            if (anyStale) {
                meta = { ...meta, stale: true };
            }

            const hasAnyData = Object.values(data).some((v) => v != null);

            peliqan.value = hasAnyData
                ? {
                      bundle: 'all',
                      data,
                      filters: filtersMeta,
                      meta,
                  }
                : null;
        } catch (e) {
            peliqan.value = null;
            bundleErrors.value = {
                _all: e?.message ?? 'MT-data laden mislukt',
            };
        } finally {
            loading.value = false;
        }
    }

    onMounted(loadPeliqan);

    watch(filtersRef, loadPeliqan, { deep: true });

    const bundleErrorMessage = (bundle) => bundleErrors.value[bundle] ?? null;

    const hasBundleErrors = () => Object.keys(bundleErrors.value).length > 0;

    const allBundlesFailed = () =>
        BUNDLES.every((b) => bundleErrors.value[b]) &&
        !peliqan.value;

    return {
        peliqan,
        peliqanLoading: loading,
        bundleErrors,
        bundleErrorMessage,
        hasBundleErrors,
        allBundlesFailed,
        reloadPeliqan: loadPeliqan,
    };
}
