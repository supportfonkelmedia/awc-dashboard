import { onMounted, ref } from 'vue';

export function useMtWmsLoader() {
    const wmsPeliqan = ref(null);
    const wmsLoading = ref(true);
    const wmsError = ref(null);

    async function loadWms() {
        wmsLoading.value = true;
        wmsError.value = null;

        try {
            const res = await fetch(route('mt.wms'), {
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

    return { wmsPeliqan, wmsLoading, wmsError, reloadWms: loadWms };
}
