import { onMounted, ref, watch } from 'vue';

export function useMtWmsLoader(filtersRef = null) {
    const wmsPeliqan = ref(null);
    const wmsLoading = ref(true);
    const wmsError = ref(null);

    function wmsYear() {
        const y = Number(filtersRef?.value?.book_year);
        if (y >= 2000 && y <= 2100) {
            return y;
        }
        return new Date().getFullYear();
    }

    async function loadWms() {
        wmsLoading.value = true;
        wmsError.value = null;

        const year = wmsYear();
        const url = `${route('mt.wms')}?year=${encodeURIComponent(String(year))}`;

        try {
            const res = await fetch(url, {
                headers: {
                    Accept: 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            });

            const json = await res.json();

            if (!res.ok) {
                wmsError.value =
                    (typeof json.error === 'string' && json.error) ||
                    `7T WMS laden mislukt (HTTP ${res.status})`;
                wmsPeliqan.value = null;
                return;
            }

            wmsPeliqan.value = json;

            const metricErrors = json?.data?.errors;
            if (metricErrors && typeof metricErrors === 'object') {
                const parts = Object.entries(metricErrors)
                    .filter(([, v]) => v)
                    .map(([k, v]) => {
                        const msg = String(v);
                        const trino = msg.match(
                            /message='([^']+)'/,
                        )?.[1];
                        return `${k}: ${trino ?? msg.slice(0, 120)}`;
                    });
                if (parts.length) {
                    wmsError.value = parts.join(' · ');
                }
            }
        } catch (e) {
            wmsError.value = e?.message ?? '7T WMS laden mislukt';
            wmsPeliqan.value = null;
        } finally {
            wmsLoading.value = false;
        }
    }

    onMounted(loadWms);

    if (filtersRef) {
        watch(
            () => filtersRef.value?.book_year,
            (next, prev) => {
                if (next != null && next !== prev) {
                    loadWms();
                }
            },
        );
    }

    return { wmsPeliqan, wmsLoading, wmsError, reloadWms: loadWms };
}
