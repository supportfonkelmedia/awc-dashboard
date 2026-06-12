import {
    computeOccupancy,
    computeStorageLeadTime,
    fmtDays,
    fmtPct,
    wmsAvailableFromPeliqan,
    wmsFromPeliqan,
} from '@/composables/useWms7tMetrics';
import { computed } from 'vue';

export function useAwcPeliqanData(peliqanRef) {
    const wms = computed(() => wmsFromPeliqan(peliqanRef.value));

    const hubspot = computed(() => {
        const data = peliqanRef.value?.data;
        if (!data) return null;
        return data.hubspot ?? null;
    });

    const schema = computed(() => peliqanRef.value?.meta?.schema ?? null);

    const occupancy = computed(() => computeOccupancy(wms.value));

    const storageLeadTime = computed(() => computeStorageLeadTime(wms.value));

    const openTickets = computed(() => {
        const rows = hubspot.value?.tickets ?? [];
        return rows.filter((t) => !t.gesloten_op).length;
    });

    const npsScore = computed(() => {
        const rows = hubspot.value?.nps ?? [];
        const scores = rows
            .map((r) => Number(r.score ?? r.score_fallback))
            .filter((n) => !Number.isNaN(n));
        if (!scores.length) return null;
        const promoters = scores.filter((s) => s >= 9).length;
        const detractors = scores.filter((s) => s <= 6).length;
        return Math.round(((promoters - detractors) / scores.length) * 100);
    });

    const wmsAvailable = computed(() =>
        wmsAvailableFromPeliqan(peliqanRef.value, wms.value),
    );

    return {
        wms,
        hubspot,
        schema,
        wmsAvailable,
        occupancy,
        storageLeadTime,
        openTickets,
        npsScore,
        fmtPct,
        fmtDays,
    };
}
