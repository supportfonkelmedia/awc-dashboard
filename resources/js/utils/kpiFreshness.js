/**
 * Overdracht: bron_bijgewerkt in UTC → Europe/Amsterdam weergave.
 *
 * @param {string|null|undefined} iso
 */
export function formatBronBijgewerkt(iso) {
    if (!iso) {
        return null;
    }
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) {
        return null;
    }

    return new Intl.DateTimeFormat('nl-NL', {
        timeZone: 'Europe/Amsterdam',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
    }).format(d);
}

/**
 * Oudste bron_bijgewerkt van getoonde tegels (meetwaarde / alle oordel op scherm).
 *
 * @param {Array<{ oordeelRow?: { bron_bijgewerkt?: string } }>} elements
 */
export function oldestBronBijgewerktLabel(elements) {
    let oldest = null;

    for (const el of elements) {
        const raw = el.oordeelRow?.bron_bijgewerkt;
        if (!raw) {
            continue;
        }
        const t = new Date(raw).getTime();
        if (Number.isNaN(t)) {
            continue;
        }
        if (oldest == null || t < oldest) {
            oldest = t;
        }
    }

    if (oldest == null) {
        return '—';
    }

    return formatBronBijgewerkt(new Date(oldest).toISOString()) ?? '—';
}
