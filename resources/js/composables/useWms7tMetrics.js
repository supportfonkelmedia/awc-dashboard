/** Shared 7T WMS metrics from Peliqan AWC handler (?bundle=wms). */

export function wmsFromPeliqan(peliqan) {
    if (!peliqan) return null;
    const data = peliqan.data;
    if (!data) return null;
    return data.wms ?? data;
}

export function wmsAvailableFromPeliqan(peliqan, wms, meta) {
    const bundle = wms ?? wmsFromPeliqan(peliqan);
    const m = meta ?? peliqan?.meta;
    return (
        bundle?.wms_available === true || m?.wms?.available === true
    );
}

export function computeOccupancy(wms) {
    if (wms?.occupancy) {
        const { total, occupied, rate } = wms.occupancy;
        return {
            total: total ?? 0,
            occupied: occupied ?? 0,
            rate:
                rate ??
                (total
                    ? Math.round((occupied / total) * 1000) / 10
                    : null),
        };
    }

    const totaal = wms?.bezetting?.locaties_totaal ?? [];
    const bezet = wms?.bezetting?.locaties_bezet ?? [];
    const bezetIds = new Set(
        bezet.map((r) => r.locatie_id).filter((id) => id != null),
    );
    const eligible = totaal.filter((r) => !r.geblokkeerd);
    const total = eligible.length;
    const occupied = eligible.filter((r) => bezetIds.has(r.locatie_id)).length;
    const rate =
        total && occupied != null
            ? Math.round((occupied / total) * 1000) / 10
            : null;
    return { total, occupied, rate };
}

function parseDate(v) {
    if (!v) return null;
    const d = new Date(v);
    return Number.isNaN(d.getTime()) ? null : d;
}

function daysBetween(a, b) {
    const da = parseDate(a);
    const db = parseDate(b);
    if (!da || !db) return null;
    return (db.getTime() - da.getTime()) / (1000 * 60 * 60 * 24);
}

export function computeStorageLeadTime(wms) {
    if (wms?.storage_lead_time_days != null) {
        return Number(wms.storage_lead_time_days);
    }

    const rows = wms?.leverdata ?? [];
    const deltas = [];
    for (const r of rows) {
        if (r.informatief) continue;
        const d = daysBetween(r.gepland, r.werkelijk);
        if (d != null && d >= 0) deltas.push(d);
    }
    if (!deltas.length) return null;
    const avg = deltas.reduce((a, b) => a + b, 0) / deltas.length;
    return Math.round(avg * 10) / 10;
}

export function fmtPct(v) {
    if (v == null || Number.isNaN(Number(v))) return null;
    return `${Number(v).toLocaleString('nl-NL', { maximumFractionDigits: 1 })}%`;
}

export function fmtDays(v) {
    if (v == null || Number.isNaN(Number(v))) return null;
    return `${Number(v).toLocaleString('nl-NL', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} dgn`;
}

/** Share of stock counts where geteld equals verwacht (7T Telling_Locaties). */
export function computeInventoryAccuracy(wms) {
    if (wms?.inventory_accuracy_pct != null) {
        return Number(wms.inventory_accuracy_pct);
    }

    const rows = wms?.tellingen ?? [];
    let match = 0;
    let total = 0;
    for (const r of rows) {
        const exp = Number(r.verwacht ?? 0);
        const got = Number(r.geteld ?? 0);
        if (exp <= 0 && got <= 0) continue;
        total += 1;
        if (exp === got) match += 1;
    }
    return total ? Math.round((match / total) * 1000) / 10 : null;
}

export function computeOntvangstenCount(wms) {
    if (wms?.ontvangsten_count != null) {
        return Number(wms.ontvangsten_count);
    }
    return (wms?.ontvangsten ?? []).length;
}

/** Dock-to-Stock payload from 7T handler (Brief Fonkel deel 3). */
export function dockToStockFromWms(wms) {
    return wms?.dock_to_stock ?? null;
}

export function fmtHours(v) {
    if (v == null || Number.isNaN(Number(v))) return null;
    return `${Number(v).toLocaleString('nl-NL', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 1,
    })} uur`;
}

/**
 * Resolve Dock-to-Stock summary for the MT filter (year / optional month).
 * Falls back to API YTD summary when month = all.
 */
export function resolveDockToStockForPeriod(d2s, applied) {
    if (!d2s) return null;

    const year = Number(applied?.book_year ?? d2s.year);
    const monthRaw = applied?.month;
    const month =
        monthRaw != null && monthRaw !== '' && monthRaw !== 'all'
            ? Number(monthRaw)
            : null;

    if (month >= 1 && month <= 12) {
        const row = (d2s.monthly ?? []).find(
            (m) => Number(m.month) === month && Number(m.year ?? year) === year,
        );
        if (row) {
            return {
                pct_within_24h: row.pct_within_24h,
                within_24h: row.within_24h,
                measurable_orders: row.orders,
                median_hours: null,
                coverage_pct: d2s.coverage_pct,
                total_unloaded: d2s.total_unloaded,
                periodLabel: `${year} · ${String(month).padStart(2, '0')}`,
                preliminary: isCurrentMonthPreliminary(year, month),
            };
        }
    }

    return {
        pct_within_24h: d2s.pct_within_24h,
        within_24h: d2s.within_24h,
        measurable_orders: d2s.measurable_orders,
        median_hours: d2s.median_hours,
        coverage_pct: d2s.coverage_pct,
        total_unloaded: d2s.total_unloaded,
        periodLabel: String(year),
        preliminary: false,
    };
}

function isCurrentMonthPreliminary(year, month) {
    const now = new Date();
    return (
        Number(year) === now.getFullYear() &&
        Number(month) === now.getMonth() + 1
    );
}

export function dockToStockMonthlyChartRows(d2s, applied) {
    if (!d2s?.monthly?.length) return [];
    const year = Number(applied?.book_year ?? d2s.year);
    const now = new Date();
    const curYear = now.getFullYear();
    const curMonth = now.getMonth() + 1;

    return [...d2s.monthly]
        .filter((m) => Number(m.year ?? year) === year)
        .sort((a, b) => Number(a.month) - Number(b.month))
        .map((m) => ({
            ...m,
            preliminary:
                Number(m.year ?? year) === curYear &&
                Number(m.month) === curMonth,
        }));
}
