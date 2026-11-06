/**
 * @param {string[]} views
 * @param {{ limit?: number }} [opts]
 * @returns {Promise<{ tables: Record<string, object[]>, error: string|null }>}
 */
export async function fetchKpiDrill(views, opts = {}) {
    if (!views?.length) {
        return { tables: {}, error: null };
    }

    const params = new URLSearchParams({
        bundle: 'drill',
        views: views.join(','),
    });
    if (opts.limit) {
        params.set('limit', String(opts.limit));
    }

    try {
        const res = await fetch(`${route('kpi.peliqan')}?${params}`, {
            headers: { Accept: 'application/json' },
            credentials: 'same-origin',
        });
        const json = await res.json();
        if (!res.ok) {
            return {
                tables: {},
                error:
                    typeof json.error === 'string'
                        ? json.error
                        : 'Drill-data laden mislukt',
            };
        }

        return { tables: json.tables ?? {}, error: null };
    } catch (e) {
        return {
            tables: {},
            error: e?.message ?? 'Drill-data laden mislukt',
        };
    }
}
