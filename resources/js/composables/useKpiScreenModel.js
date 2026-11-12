import { computed } from 'vue';
import {
    deltaSentiment,
    formatKpiDelta,
    formatKpiValue,
    formatStandPer,
    pctChangeFromDelta,
    splitKpiValue,
    STATE_LABELS,
} from '@/utils/kpiFormat';
import { oldestBronBijgewerktLabel } from '@/utils/kpiFreshness';
import { scopeLabel } from '@/constants/kpiEntiteiten';

/**
 * @param {Record<string, unknown>|null|undefined} row
 */
function normScope(row) {
    if (!row) {
        return '';
    }
    const s = row.scope_code;

    return s == null ? '' : String(s);
}

/**
 * `pijler` uit config. Live warehouse: alleen het thema ("Financiële gezondheid",
 * "Waarde", "1 · Bewustwording") komt als thema op de tegel. Optioneel "SECTIE: thema"
 * om een expliciete schermsectie af te dwingen.
 *
 * @param {string} pijlerRaw
 * @returns {{ sectionKey: string | null, themeLabel: string | null }}
 */
export function parsePijlerParts(pijlerRaw) {
    const raw = pijlerRaw == null || String(pijlerRaw).trim() === '' ? '' : String(pijlerRaw).trim();
    if (!raw || raw.toLowerCase() === 'sectie') {
        return { sectionKey: null, themeLabel: null };
    }
    const idx = raw.indexOf(':');
    if (idx === -1) {
        return { sectionKey: null, themeLabel: raw };
    }

    return {
        sectionKey: raw.slice(0, idx).trim().toUpperCase() || null,
        themeLabel: raw.slice(idx + 1).trim() || null,
    };
}

const AANVULLEND_KPI = new Set(['omzet_brug', 'ab_players', 'enps']);

/**
 * Schermsectie van een tegel (mockup 01: strategisch = MT-KPI's + AANVULLEND "Omzet en mensen").
 * Expliciete "SECTIE:" prefix in `pijler` wint; andere schermen hebben één sectie.
 *
 * @param {string} scherm
 * @param {{ sectionKey: string | null, kpiCode: string | null, element: string }} row
 */
function resolveSectionKey(scherm, row) {
    if (row.sectionKey) {
        return row.sectionKey;
    }
    if (scherm === 'strategisch') {
        if (row.element === 'banner' || AANVULLEND_KPI.has(row.kpiCode ?? '')) {
            return 'AANVULLEND';
        }

        return 'STRATEGISCH';
    }

    return 'KPI';
}

/**
 * Mockup-volgorde strategisch: 6 MT-KPI-tegels → Omzetbrug-banner → A/B Players.
 * Lost omzetbrug `positie`=0 niet meer bovenaan (Peliqan Overdracht-tabel).
 *
 * @param {string|null|undefined} scherm
 * @param {Array<{ element: string, kpiCode: string | null, positie: number }>} items
 */
function sortStrategischMainGrid(scherm, items) {
    if (scherm !== 'strategisch') {
        return items;
    }

    const key = (row) => {
        const k = row.kpiCode ?? '';
        if (row.element === 'banner' && k === 'omzet_brug') {
            return 70;
        }
        if (k === 'ab_players') {
            return 80;
        }
        const order = {
            bruto_marge_per_loonkosten: 10,
            triple_lob: 20,
            winrate: 30,
            churn: 40,
            otif: 50,
            ebitda: 60,
        };

        return order[k] ?? 35;
    };

    return [...items].sort((a, b) => {
        const ka = key(a);
        const kb = key(b);
        if (ka !== kb) {
            return ka - kb;
        }

        return a.positie - b.positie;
    });
}

/**
 * @param {string} sectionKey
 */
function sectionDisplayHeading(sectionKey) {
    if (sectionKey === 'STRATEGISCH') {
        return 'STRATEGISCH: MT-KPI\'s';
    }
    if (sectionKey === 'AANVULLEND') {
        return 'AANVULLEND: Omzet en mensen';
    }

    return sectionKey;
}

/**
 * @param {Array<Record<string, unknown>>} oordelen
 * @param {string|null|undefined} kpiCode
 * @param {string|null|undefined} scopeCode
 */
export function findOordeelRow(oordelen, kpiCode, scopeCode) {
    if (!kpiCode) {
        return null;
    }
    // Overdracht: match on kpi_code + COALESCE(scope_code, ''), exact only.
    // No fallback to "the only row for this kpi_code": that would show e.g. the
    // concern winrate on the AFC tile. A missing row must become data_ontbreekt.
    const scope = scopeCode == null ? '' : String(scopeCode);

    return (
        oordelen.find(
            (r) => r.kpi_code === kpiCode && normScope(r) === scope,
        ) ?? null
    );
}

/**
 * @param {Array<Record<string, unknown>>} trends
 * @param {string|null|undefined} kpiCode
 * @param {string|null|undefined} scopeCode
 */
export function filterTrendPoints(trends, kpiCode, scopeCode) {
    if (!kpiCode) {
        return [];
    }
    const scope = scopeCode == null ? '' : String(scopeCode);

    return trends
        .filter(
            (t) =>
                t.kpi_code === kpiCode &&
                normScope(t) === scope,
        )
        .sort((a, b) => {
            const pa = String(a.periode ?? '');
            const pb = String(b.periode ?? '');
            if (pa !== pb) {
                return pa.localeCompare(pb);
            }

            return Number(a.volgnummer ?? 0) - Number(b.volgnummer ?? 0);
        });
}

/**
 * PERIODE-filter (mockup 01): alleen de grafieken volgen de gekozen periode; de
 * tegelwaarde houdt zijn vaste venster. Dit is filteren, geen rekenen.
 *
 * @param {Array<Record<string, unknown>>} points
 * @param {string} periode 'all' of een jaartal '2026'
 */
export function filterTrendByPeriode(points, periode) {
    if (!periode || periode === 'all') {
        return points;
    }

    return points.filter((p) => String(p.periode ?? '').startsWith(periode));
}

/**
 * @param {Array<Record<string, unknown>>} trends
 * @returns {string[]} jaartallen, nieuwste eerst
 */
export function trendYears(trends) {
    const years = new Set();
    for (const t of trends) {
        const y = String(t.periode ?? '').slice(0, 4);
        if (/^\d{4}$/.test(y)) {
            years.add(y);
        }
    }

    return [...years].sort().reverse();
}

/**
 * Group trend by serie for multi-line charts.
 *
 * @param {Array<Record<string, unknown>>} points
 */
export function groupTrendSeries(points) {
    /** @type {Record<string, Array<Record<string, unknown>>>} */
    const bySerie = {};
    for (const p of points) {
        const key = p.serie == null || p.serie === '' ? '' : String(p.serie);
        if (!bySerie[key]) {
            bySerie[key] = [];
        }
        bySerie[key].push(p);
    }

    return Object.entries(bySerie).map(([serie, pts]) => ({
        serie: serie || null,
        points: pts,
    }));
}

/**
 * @param {Record<string, unknown>} configRow
 * @param {Record<string, unknown>|null} oordeelRow
 */
function resolveTile(configRow, oordeelRow) {
    const waardeBron = String(configRow.waarde_bron ?? 'kpi_oordeel');

    if (waardeBron === 'vast') {
        return {
            display: 'status',
            state: String(configRow.vaste_staat ?? 'in_opbouw'),
            bodyText: String(configRow.vaste_tekst ?? ''),
            showValue: false,
        };
    }

    const handmatigKpiCodes = new Set(['enps', 'ab_players', 'ebitda']);
    const configKpiCode = configRow.kpi_code ? String(configRow.kpi_code) : '';

    if (!oordeelRow) {
        return {
            display: 'status',
            state: 'data_ontbreekt',
            bodyText:
                'Geen gegevens gevonden. Meld dit aan Chloë.',
            showValue: false,
            showInvoerKnop: handmatigKpiCodes.has(configKpiCode),
        };
    }

    if (oordeelRow.tonen_op_dashboard === false) {
        return { display: 'hidden' };
    }

    // kpi_betrouwbaarheid: een onbetrouwbaar cijfer nooit tonen, ook als weergave nog meetwaarde zegt.
    if (oordeelRow.betrouwbaarheid === 'onbetrouwbaar') {
        return {
            display: 'status',
            state: 'onbetrouwbaar',
            bodyText: String(oordeelRow.betrouwbaarheid_reden ?? oordeelRow.leeg_reden ?? ''),
            showValue: false,
        };
    }

    const weergave = String(oordeelRow.weergave ?? '');

    if (weergave === 'meetwaarde') {
        if (oordeelRow.waarde == null || oordeelRow.waarde === '') {
            return {
                display: 'status',
                state: 'data_ontbreekt',
                bodyText:
                    'Geen gegevens gevonden. Meld dit aan Chloë.',
                showValue: false,
            };
        }

        return {
            display: 'value',
            state: 'meetwaarde',
            showValue: true,
        };
    }

    if (weergave === 'gepland_2027') {
        return { display: 'hidden' };
    }

    return {
        display: 'status',
        state: weergave,
        bodyText: String(oordeelRow.leeg_reden ?? ''),
        showValue: false,
        showInvoerKnop:
            weergave === 'wacht_op_invoer' ||
            (weergave === 'data_ontbreekt' &&
                handmatigKpiCodes.has(configKpiCode)),
    };
}

/**
 * Trendrijen uit de drill-route samenvoegen met die van het scherm, zonder dubbele punten.
 *
 * @param {Array<Record<string, unknown>>} base
 * @param {Array<Record<string, unknown>>} extra
 */
function mergeTrends(base, extra) {
    if (!extra?.length) {
        return base;
    }
    const key = (r) =>
        `${r.kpi_code}|${r.scope_code ?? ''}|${r.serie ?? ''}|${r.periode}`;
    const seen = new Set(base.map(key));

    return [...base, ...extra.filter((r) => !seen.has(key(r)))];
}

/**
 * Entiteitfilter (alleen strategisch): een tegel schakelt naar de gekozen entiteit
 * als kpi_oordeel daar een rij voor heeft. Anders blijft de tegel staan met een notitie,
 * zodat niemand een concerncijfer voor een entiteitcijfer aanziet.
 *
 * @param {Record<string, unknown>} row tegel_config-rij
 * @param {Array<Record<string, unknown>>} oordelen
 * @param {string} entiteit scope_code, of 'concern'
 * @returns {{ row: Record<string, unknown>, note: string|null }}
 */
function applyEntiteit(row, oordelen, entiteit) {
    if (entiteit === 'concern' || !row.kpi_code) {
        return { row, note: null };
    }
    const kpiCode = String(row.kpi_code);
    if (findOordeelRow(oordelen, kpiCode, entiteit)) {
        return {
            row: {
                ...row,
                scope_code: entiteit,
                trend_scope_code: row.trend_kpi_code ? entiteit : row.trend_scope_code,
                titel: `${row.titel ?? ''}, ${scopeLabel(entiteit)}`,
            },
            note: null,
        };
    }
    const huidige = row.scope_code == null ? '' : String(row.scope_code);

    return {
        row,
        note: huidige
            ? `Niet per entiteit beschikbaar; toont ${huidige === 'concern' ? 'het concern' : scopeLabel(huidige)}.`
            : 'Niet per entiteit beschikbaar.',
    };
}

/**
 * @param {import('vue').Ref<object|null>} payloadRef
 * @param {import('vue').Ref<string>} [periodeRef] 'all' | '2026', alleen voor trendlijnen
 * @param {import('vue').Ref<string>} [entiteitRef] scope_code of 'concern', alleen strategisch
 * @param {import('vue').Ref<Array<object>>} [extraTrendsRef] trendrijen voor andere entiteiten
 */
export function useKpiScreenModel(
    payloadRef,
    periodeRef = null,
    entiteitRef = null,
    extraTrendsRef = null,
) {
    const elements = computed(() => {
        const payload = payloadRef.value;
        if (!payload) {
            return [];
        }

        const periode = periodeRef?.value ?? 'all';
        const scherm = payload.scherm ? String(payload.scherm) : '';
        const config = payload.tegel_config ?? [];
        const oordelen = payload.kpi_oordeel ?? [];
        const trends = mergeTrends(payload.kpi_trend ?? [], extraTrendsRef?.value ?? []);
        const entiteit =
            scherm === 'strategisch' ? (entiteitRef?.value ?? 'concern') : 'concern';

        /** @type {Array<object>} */
        const out = [];

        for (const configRow of config) {
            const element = String(configRow.element ?? 'tegel');
            if (element === 'header') {
                continue;
            }

            const { row, note: entiteitNote } =
                element === 'tegel' || element === 'banner'
                    ? applyEntiteit(configRow, oordelen, entiteit)
                    : { row: configRow, note: null };

            const oordeelRow =
                row.kpi_code != null && row.kpi_code !== ''
                    ? findOordeelRow(oordelen, String(row.kpi_code), row.scope_code)
                    : null;

            const resolved = resolveTile(row, oordeelRow);
            if (resolved.display === 'hidden') {
                continue;
            }

            const trendCode = row.trend_kpi_code
                ? String(row.trend_kpi_code)
                : null;
            const trendScope =
                row.trend_scope_code != null
                    ? String(row.trend_scope_code)
                    : row.scope_code != null
                      ? String(row.scope_code)
                      : '';
            const trendPointsAll = trendCode
                ? filterTrendPoints(trends, trendCode, trendScope)
                : [];
            const trendPoints = filterTrendByPeriode(trendPointsAll, periode);
            const trendSeries = groupTrendSeries(trendPoints);
            const trendFilteredOut =
                trendPointsAll.length > 0 && trendPoints.length === 0;

            const eenheid = oordeelRow?.eenheid
                ? String(oordeelRow.eenheid)
                : null;
            const waarde = oordeelRow?.waarde != null ? Number(oordeelRow.waarde) : null;
            const waardeVorige =
                oordeelRow?.waarde_vorige != null
                    ? Number(oordeelRow.waarde_vorige)
                    : null;
            const deltaRaw =
                oordeelRow?.delta != null ? Number(oordeelRow.delta) : null;

            let valueFormatted = null;
            let valueNumber = null;
            let valueUnit = null;
            let deltaFormatted = null;
            let deltaTone = 'neutral';

            if (resolved.display === 'value' && eenheid) {
                valueFormatted = formatKpiValue(eenheid, waarde);
                const split = splitKpiValue(eenheid, waarde);
                valueNumber = split.number;
                valueUnit = split.unit;
                if (
                    waardeVorige != null &&
                    !Number.isNaN(waardeVorige) &&
                    deltaRaw != null
                ) {
                    const d = formatKpiDelta(eenheid, deltaRaw);
                    if (d) {
                        let text = d.text;
                        if (
                            (eenheid === 'euro' || eenheid === 'aantal') &&
                            d.rawDelta != null
                        ) {
                            const pct = pctChangeFromDelta(
                                deltaRaw,
                                waardeVorige,
                            );
                            if (pct != null) {
                                const pctSign = pct > 0 ? '+' : '';
                                text = `${text} (${pctSign}${pct}%)`;
                            }
                            text += ' t.o.v. vorige maand';
                        } else if (
                            eenheid === 'ratio' ||
                            eenheid === 'procent' ||
                            eenheid === 'dagen' ||
                            eenheid === 'score'
                        ) {
                            if (!text.includes('t.o.v.')) {
                                text += ' t.o.v. vorige maand';
                            }
                        }
                        deltaFormatted = text;
                        deltaTone = deltaSentiment(
                            String(oordeelRow?.richting ?? 'neutraal'),
                            d.direction,
                        );
                    }
                }
            }

            const stateLabel =
                STATE_LABELS[resolved.state] ?? resolved.state;

            const pijlerRaw = row.pijler ? String(row.pijler) : '';
            const parsedPijler = parsePijlerParts(pijlerRaw);
            const explicitSection = parsedPijler.sectionKey;
            // Warehouse zet soms het elementtype in pijler ("banner"), geen thema.
            const themeLabel =
                parsedPijler.themeLabel &&
                parsedPijler.themeLabel.toLowerCase() !== element
                    ? parsedPijler.themeLabel
                    : null;
            const kpiCode = row.kpi_code ? String(row.kpi_code) : null;
            const sectionKey = resolveSectionKey(scherm, {
                sectionKey: explicitSection,
                kpiCode,
                element,
            });

            out.push({
                // scope in de key: bij een andere entiteit mount de tegel/banner opnieuw.
                key: `${row.scherm}-${row.positie}-${row.kpi_code ?? row.titel}-${normScope(row)}`,
                entiteitNote,
                element,
                positie: Number(row.positie ?? 0),
                pijler: pijlerRaw,
                sectionKey,
                themeLabel,
                aanname: oordeelRow?.aanname ? String(oordeelRow.aanname) : null,
                betrouwbaarheid: oordeelRow?.betrouwbaarheid
                    ? String(oordeelRow.betrouwbaarheid)
                    : null,
                betrouwbaarheidReden: oordeelRow?.betrouwbaarheid_reden
                    ? String(oordeelRow.betrouwbaarheid_reden)
                    : null,
                kanttekening: oordeelRow?.kanttekening
                    ? String(oordeelRow.kanttekening)
                    : null,
                titel: String(row.titel ?? ''),
                eigenaar: oordeelRow?.eigenaar
                    ? String(oordeelRow.eigenaar)
                    : '',
                bronLabel: row.bron_label ? String(row.bron_label) : '',
                venster: oordeelRow?.venster ? String(oordeelRow.venster) : '',
                toelichting: oordeelRow?.toelichting
                    ? String(oordeelRow.toelichting)
                    : '',
                standPer: formatStandPer(
                    oordeelRow?.stand_per ? String(oordeelRow.stand_per) : null,
                ),
                resolved,
                stateLabel,
                valueFormatted,
                valueNumber,
                valueUnit,
                deltaFormatted,
                deltaTone,
                goalStatus:
                    resolved.state !== 'onbetrouwbaar' && oordeelRow?.status
                        ? String(oordeelRow.status)
                        : null,
                goalDoelTekst: oordeelRow?.doel_tekst
                    ? String(oordeelRow.doel_tekst)
                    : null,
                eenheid: oordeelRow?.eenheid ? String(oordeelRow.eenheid) : null,
                trendSeries,
                trendFilteredOut,
                trendPeriode: periode,
                drillViews: row.drill_views
                    ? String(row.drill_views)
                          .split(',')
                          .map((s) => s.trim())
                          .filter(Boolean)
                    : [],
                kpiCode,
                scopeCode: normScope(row),
                configRow: row,
                oordeelRow,
            });
        }

        const sorted = out.sort((a, b) => a.positie - b.positie);
        const main = sorted.filter(
            (e) => e.element === 'banner' || e.element === 'tegel',
        );
        const rest = sorted.filter(
            (e) => e.element !== 'banner' && e.element !== 'tegel',
        );

        return [...sortStrategischMainGrid(scherm, main), ...rest];
    });

    const banners = computed(() =>
        elements.value.filter((e) => e.element === 'banner'),
    );

    const tiles = computed(() =>
        elements.value.filter((e) => e.element === 'tegel'),
    );

    /**
     * Rows for the main grid in config order: banners are not all rendered first:
     * they stay in `positie` with tegels (mockup: strategische tegels, then Omzetbrug banner + A/B).
     *
     * @type {import('vue').ComputedRef<Array<{ pijler: string, items: object[] }>>}
     */
    const layoutRowGroups = computed(() => {
        const rows = elements.value.filter(
            (e) => e.element === 'banner' || e.element === 'tegel',
        );
        /** @type {Array<{ sectionKey: string, sectionHeading: string, items: object[] }>} */
        const groups = [];

        for (const row of rows) {
            const sectionKey = row.sectionKey || 'KPI';
            let group = groups.find((g) => g.sectionKey === sectionKey);
            if (!group) {
                group = {
                    sectionKey,
                    sectionHeading: sectionDisplayHeading(sectionKey),
                    items: [],
                };
                groups.push(group);
            }
            group.items.push(row);
        }

        return groups;
    });

    const sections = computed(() =>
        elements.value.filter((e) => e.element === 'sectie'),
    );

    const gepland2027 = computed(() => {
        const oordelen = payloadRef.value?.kpi_oordeel ?? [];

        return oordelen.filter(
            (r) => String(r.weergave ?? '') === 'gepland_2027',
        );
    });

    const bijgewerktLabel = computed(() =>
        oldestBronBijgewerktLabel(elements.value),
    );

    /** Jaartallen in kpi_trend van dit scherm (voor de PERIODE-keuze). */
    const periodeOptions = computed(() =>
        trendYears(payloadRef.value?.kpi_trend ?? []),
    );

    return {
        elements,
        banners,
        tiles,
        layoutRowGroups,
        sections,
        gepland2027,
        bijgewerktLabel,
        periodeOptions,
    };
}
