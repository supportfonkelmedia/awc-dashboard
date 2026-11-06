import { ref, watch } from 'vue';

/**
 * Loads KPI screen payload from Laravel → Peliqan (bundle=screen).
 *
 * @param {import('vue').Ref<string>|string} schermRef
 */
export function useKpiScreenLoader(schermRef) {
    const loading = ref(false);
    const error = ref(null);
    const payload = ref(null);

    async function load(scherm) {
        if (!scherm) {
            return;
        }

        loading.value = true;
        error.value = null;

        try {
            const params = new URLSearchParams({
                bundle: 'screen',
                scherm,
            });
            const res = await fetch(`${route('kpi.peliqan')}?${params}`, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin',
            });

            const json = await res.json();

            if (!res.ok) {
                error.value =
                    typeof json.error === 'string'
                        ? json.error
                        : json.message ?? `HTTP ${res.status}`;
                payload.value = null;

                return;
            }

            payload.value = json;
        } catch (e) {
            error.value = e?.message ?? 'Kon KPI-data niet laden.';
            payload.value = null;
        } finally {
            loading.value = false;
        }
    }

    watch(
        schermRef,
        (s) => {
            load(s);
        },
        { immediate: true },
    );

    return { loading, error, payload, reload: () => load(typeof schermRef === 'string' ? schermRef : schermRef.value) };
}
