import {
    CUSTOMER_JOURNEY_STAGES,
    ENTITY_KPIS,
    KPI_STATUS,
    OPERATIONAL_KPIS,
    STRATEGIC_KPI_ORDER,
    STRATEGIC_KPIS,
    TACTICAL_KPIS,
    kpiExplain,
    strategicLinkLabel,
} from '@/config/mtKpiFramework';
import {
    computeInventoryAccuracy,
    computeOccupancy,
    computeOntvangstenCount,
    computeStorageLeadTime,
    fmtDays,
    fmtPct,
    wmsAvailableFromPeliqan,
    wmsFromPeliqan,
} from '@/composables/useWms7tMetrics';
import { computed } from 'vue';

function fmtEur(n) {
    if (n == null || Number.isNaN(Number(n))) return null;
    const v = Number(n);
    if (Math.abs(v) >= 1_000_000) return `€${(v / 1_000_000).toFixed(2)}M`;
    if (Math.abs(v) >= 1_000)
        return `€${(v / 1_000).toFixed(1)}K`.replace('.', ',');
    return `€${Math.round(v).toLocaleString('nl-NL')}`;
}

function deltaTxt(cur, prev) {
    if (prev == null || Number(prev) === 0 || cur == null) return '';
    const p =
        ((Number(cur) - Number(prev)) / Math.abs(Number(prev))) * 100;
    return `${p >= 0 ? '+' : ''}${p.toFixed(1)}%`;
}

function deltaPositive(cur, prev) {
    if (prev == null || Number(prev) === 0) return true;
    return Number(cur) >= Number(prev);
}

function kpi(def, overrides = {}) {
    const explain = kpiExplain(def.id);
    return {
        id: def.id,
        title: def.label,
        theme: def.theme ?? null,
        status: overrides.status ?? def.defaultStatus,
        value: overrides.value ?? null,
        delta: overrides.delta ?? '',
        deltaPositive: overrides.deltaPositive ?? true,
        footer: overrides.footer ?? def.source ?? '',
        note: overrides.note ?? def.note ?? null,
        source: overrides.source ?? def.source ?? null,
        description: explain?.description ?? null,
        method: explain?.method ?? null,
        strategicLink: def.strategicLink
            ? strategicLinkLabel(def.strategicLink)
            : null,
        strategicLinkId: def.strategicLink ?? null,
    };
}

export function useMtKpiData(peliqanRef, appliedRef, wmsPeliqanRef = null, wmsLoadingRef = null) {
    const cw = computed(() => peliqanRef.value?.data?.cashweb ?? null);
    const hs = computed(() => peliqanRef.value?.data?.hubspot ?? null);
    const sp = computed(() => peliqanRef.value?.data?.sprinter ?? null);
    const wmsLoading = computed(() => wmsLoadingRef?.value ?? false);
    const wmsMeta = computed(
        () => wmsPeliqanRef?.value?.meta ?? peliqanRef.value?.meta ?? null,
    );
    const wms = computed(() => {
        if (wmsPeliqanRef?.value) {
            return wmsFromPeliqan(wmsPeliqanRef.value);
        }
        return wmsFromPeliqan(peliqanRef.value);
    });
    const wmsAvailable = computed(() =>
        wmsAvailableFromPeliqan(
            wmsPeliqanRef?.value ?? peliqanRef.value,
            wms.value,
            wmsMeta.value,
        ),
    );
    const occupancy = computed(() => computeOccupancy(wms.value));
    const storageLeadTime = computed(() => computeStorageLeadTime(wms.value));
    const inventoryAccuracy = computed(() =>
        computeInventoryAccuracy(wms.value),
    );
    const applied = computed(() => appliedRef.value ?? null);

    const aggregates = computed(() => cw.value?.aggregates ?? null);

    const tripleLob = computed(() => {
        const rows = cw.value?.triple_lob_customers ?? [];
        const nAll = rows.length;
        let nTriple = 0;
        let omzTriple = 0;
        let omzAll = 0;
        for (const r of rows) {
            const o = Number(r.omzet ?? 0);
            omzAll += o;
            if (Number(r.aantal_lob) >= 3) {
                nTriple += 1;
                omzTriple += o;
            }
        }
        return {
            nAll,
            nTriple,
            pctKlant: nAll ? Math.round((nTriple / nAll) * 1000) / 10 : 0,
            pctOmz: omzAll ? Math.round((omzTriple / omzAll) * 1000) / 10 : 0,
        };
    });

    function fmtEurDisplay(n) {
        return fmtEur(n) ?? '—';
    }

    function buildLobRowsFromDetail(rows, prevMap = {}) {
        const map = {};
        const admin = {};
        for (const r of rows) {
            const lob =
                (r.sub_administration && String(r.sub_administration).trim()) ||
                r.admin_code ||
                '—';
            map[lob] = (map[lob] || 0) + Number(r.debet ?? 0);
            if (!admin[lob] && r.admin_code) admin[lob] = r.admin_code;
        }
        const tot = Object.values(map).reduce((s, v) => s + v, 0);
        const totV = Object.values(prevMap).reduce((s, v) => s + v, 0);
        return Object.entries(map)
            .sort((a, b) => b[1] - a[1])
            .map(([lob, omzet]) => {
                const omzet_vorig = prevMap[lob] ?? 0;
                const delta_pct =
                    omzet_vorig > 0
                        ? ((omzet - omzet_vorig) / Math.abs(omzet_vorig)) *
                          100
                        : null;
                return {
                    lob,
                    admin_code: admin[lob] ?? '',
                    omzet,
                    omzet_vorig,
                    aandeel_pct: tot > 0 ? (omzet / tot) * 100 : 0,
                    delta_pct,
                    totaal: tot,
                    totaal_vorig: totV,
                };
            });
    }

    function formatLobPanelRow(r, tot, totV) {
        const delta_pct = r.delta_pct;
        return {
            lob: r.lob,
            admin_code: r.admin_code ?? '',
            omzet: r.omzet,
            omzet_fmt: fmtEurDisplay(r.omzet),
            omzet_vorig: r.omzet_vorig,
            omzet_vorig_fmt: r.omzet_vorig
                ? fmtEurDisplay(r.omzet_vorig)
                : '—',
            aandeel_pct: r.aandeel_pct,
            aandeel_pct_fmt: `${Number(r.aandeel_pct).toFixed(1)}%`,
            delta_pct,
            delta_fmt:
                delta_pct != null
                    ? `${delta_pct >= 0 ? '+' : ''}${Number(delta_pct).toFixed(1)}%`
                    : '',
            delta_positive: delta_pct == null || delta_pct >= 0,
        };
    }

    const revenuePerLobPanel = computed(() => {
        const def = STRATEGIC_KPIS.revenue_per_lob;
        const period =
            applied.value?.period_label ??
            applied.value?.book_periods ??
            '';
        const api = cw.value?.revenue_per_lob;

        if (api?.rows?.length) {
            const tot = Number(api.totaal ?? 0);
            const totV = Number(api.totaal_vorig ?? 0);
            const deltaTotaal = api.delta_totaal_pct;
            return {
                status: KPI_STATUS.LIVE,
                lobField: api.lob_field ?? def.note,
                periodLabel: period,
                totaalFmt: fmtEurDisplay(tot),
                totaalVorigFmt: totV ? fmtEurDisplay(totV) : '—',
                deltaTotaalFmt:
                    deltaTotaal != null
                        ? `${deltaTotaal >= 0 ? '+' : ''}${deltaTotaal}%`
                        : '',
                deltaTotaalPositive: deltaTotaal == null || deltaTotaal >= 0,
                rows: api.rows.map((r) =>
                    formatLobPanelRow(
                        {
                            lob: r.lob,
                            admin_code: r.admin_code,
                            omzet: Number(r.omzet ?? 0),
                            omzet_vorig: Number(r.omzet_vorig ?? 0),
                            aandeel_pct: Number(r.aandeel_pct ?? 0),
                            delta_pct:
                                r.delta_pct != null
                                    ? Number(r.delta_pct)
                                    : null,
                        },
                        tot,
                        totV,
                    ),
                ),
                note: null,
            };
        }

        const built = buildLobRowsFromDetail(cw.value?.omzet_detail ?? []);
        if (built.length) {
            const tot = built[0]?.totaal ?? 0;
            return {
                status: KPI_STATUS.IN_DEVELOPMENT,
                lobField:
                    'sub_administration (fallback: admin_code) — YoY per LOB na Peliqan-deploy',
                periodLabel: period,
                totaalFmt: fmtEurDisplay(tot),
                totaalVorigFmt: '—',
                deltaTotaalFmt: '',
                deltaTotaalPositive: true,
                rows: built.map((r) =>
                    formatLobPanelRow(r, tot, 0),
                ),
                note: 'Huidige periode alleen; deploy peliqan_mt_api_handler voor YoY per LOB.',
            };
        }

        return {
            status: KPI_STATUS.IN_DEVELOPMENT,
            lobField: def.source,
            periodLabel: period,
            totaalFmt: null,
            totaalVorigFmt: '—',
            deltaTotaalFmt: '',
            deltaTotaalPositive: true,
            rows: [],
            note: 'Geen omzet in geselecteerde Cashweb-periode.',
        };
    });

    const loonTotaal = computed(() => {
        const mpl = cw.value?.marge_per_loon;
        if (mpl?.totals?.loonkosten != null) {
            return Number(mpl.totals.loonkosten);
        }
        let s = 0;
        for (const r of cw.value?.salarissen_SAL ?? []) {
            s += Number(r.loon_debet ?? 0);
        }
        return s;
    });

    const winratePipelines = computed(() => {
        const current = hs.value?.winrate_by_pipeline ?? [];
        const prior = hs.value?.winrate_by_pipeline_prior ?? [];
        const priorMap = Object.fromEntries(
            prior.map((r) => [r.pipeline_label, r]),
        );
        return current.map((r) => ({
            ...r,
            prior: priorMap[r.pipeline_label] ?? null,
        }));
    });

    const winratePeriodLabel = computed(
        () =>
            hs.value?.winrate_period_label ??
            applied.value?.winrate_period_label ??
            '',
    );

    const margePerLoonPanel = computed(() => {
        const mpl = cw.value?.marge_per_loon;
        if (!mpl?.entities?.length) {
            return {
                status: KPI_STATUS.IN_DEVELOPMENT,
                periodLabel: applied.value?.period_label ?? '',
                entities: [],
                totals: null,
                partialAccounts: [],
            };
        }
        const partial = mpl.partial_wage_accounts ?? ['4130', '4512'];
        return {
            status: KPI_STATUS.LIVE,
            periodLabel: applied.value?.period_label ?? '',
            entities: mpl.entities.map((e) => ({
                ...e,
                kpi_fmt:
                    e.kpi != null
                        ? `${Number(e.kpi).toFixed(2).replace('.', ',')}×`
                        : '—',
                bruto_marge_fmt: fmtEurDisplay(e.bruto_marge),
                loonkosten_fmt: fmtEurDisplay(e.loonkosten),
                months: (e.months ?? []).map((m) => ({
                    ...m,
                    omzet_fmt: fmtEurDisplay(m.omzet),
                    inkoop_fmt: fmtEurDisplay(m.inkoop),
                    bruto_marge_fmt: fmtEurDisplay(m.bruto_marge),
                    loonkosten_fmt: fmtEurDisplay(m.loonkosten),
                    kpi_fmt:
                        m.kpi != null
                            ? `${Number(m.kpi).toFixed(2).replace('.', ',')}×`
                            : '—',
                })),
            })),
            totals: mpl.totals
                ? {
                      ...mpl.totals,
                      kpi_fmt:
                          mpl.totals.kpi != null
                              ? `${Number(mpl.totals.kpi).toFixed(2).replace('.', ',')}×`
                              : '—',
                      bruto_marge_fmt: fmtEurDisplay(mpl.totals.bruto_marge),
                      loonkosten_fmt: fmtEurDisplay(mpl.totals.loonkosten),
                  }
                : null,
            partialAccounts: partial,
        };
    });

    const dealKpis = computed(() => {
        const pipelines = winratePipelines.value;
        if (pipelines.length) {
            let won = 0;
            let lost = 0;
            let wonV = 0;
            let lostV = 0;
            for (const p of pipelines) {
                won += Number(p.gewonnen ?? 0);
                lost += Number(p.verloren ?? 0);
                wonV += Number(p.prior?.gewonnen ?? 0);
                lostV += Number(p.prior?.verloren ?? 0);
            }
            const n = won + lost;
            const nV = wonV + lostV;
            const wr = n ? Math.round((won / n) * 1000) / 10 : 0;
            const wrV = nV ? Math.round((wonV / nV) * 1000) / 10 : 0;
            return { n, won, lost, wr, nV, wonV, lostV, wrV, pipelines };
        }
        const d = hs.value?.deals ?? [];
        const n = d.length;
        const won = d.filter(
            (x) => String(x.hs_is_closed_won) === 'true',
        ).length;
        const lost = d.filter(
            (x) => String(x.hs_is_closed_lost) === 'true',
        ).length;
        const wr = n ? Math.round((won / n) * 1000) / 10 : 0;
        const dealsYoY = hs.value?.deals_yoy_counts?.[0] ?? {};
        const nV = Number(dealsYoY?.won ?? 0) + Number(dealsYoY?.lost ?? 0);
        const wonV = Number(dealsYoY?.won ?? 0);
        const lostV = Number(dealsYoY?.lost ?? 0);
        const wrV = nV ? Math.round((wonV / nV) * 1000) / 10 : 0;
        return { n, won, lost, wr, nV, wonV, lostV, wrV, pipelines: [] };
    });

    const ticketsYoY = computed(() =>
        Number(hs.value?.tickets_yoy_count?.[0]?.n ?? 0),
    );

    const ticketKpis = computed(() => {
        const t = hs.value?.tickets ?? [];
        const n = t.length;
        let open = 0;
        for (const row of t) {
            if (!row.closed_date) open += 1;
        }
        return { n, open, closed: n - open };
    });

    const shipRows = computed(() => sp.value?.shipments ?? []);
    const shipAgg = computed(() => sp.value?.shipments_yoy_aggregate?.[0] ?? {});

    const sprinterSummary = computed(() => {
        const rows = shipRows.value;
        const n = rows.length;
        let gpm = 0;
        for (const r of rows) {
            gpm += Number(r.total_gpm_amount ?? 0);
        }
        const nYoY = Number(shipAgg.value?.n ?? 0);
        const gpmYoY = Number(shipAgg.value?.marge ?? 0);
        const avgGpm = n ? gpm / n : null;
        return { n, gpm, nYoY, gpmYoY, avgGpm };
    });

    const strategicCards = computed(() => {
        const a = aggregates.value;
        const tl = tripleLob.value;
        const mpl = margePerLoonPanel.value;
        const period = applied.value?.book_periods ?? '';

        const margePerLoonRatio =
            mpl.totals?.kpi != null
                ? Number(mpl.totals.kpi)
                : a && loonTotaal.value > 0
                  ? Number(a.brutomarge) / loonTotaal.value
                  : null;
        const margePerLoon =
            margePerLoonRatio != null
                ? `${margePerLoonRatio.toFixed(2).replace('.', ',')}×`
                : null;
        const margeFooter = mpl.totals
            ? `Brutomarge ${mpl.totals.bruto_marge_fmt} / loon ${mpl.totals.loonkosten_fmt} · ${period}`
            : a && loonTotaal.value > 0
              ? `Brutomarge ${fmtEur(a.brutomarge)} / loon ${fmtEur(loonTotaal.value)} · ${period}`
              : period;

        return STRATEGIC_KPI_ORDER.filter(
            (id) => id !== 'revenue_per_lob',
        ).map((id) => {
            const def = STRATEGIC_KPIS[id];
            switch (id) {
                case 'ebitda':
                    return kpi(def, {
                        status: KPI_STATUS.TO_DEFINE,
                        footer: `${def.source} · ${period}`,
                    });
                case 'ltv_triple_lob':
                    return kpi(def, {
                        status: KPI_STATUS.IN_DEVELOPMENT,
                        note: tl.nAll
                            ? `${tl.nTriple} triple-LOB klanten (${tl.pctKlant}% van ${tl.nAll}) — geen LTV-formule`
                            : 'Triple LOB nog valideren in Cashweb.',
                        footer: def.source,
                    });
                case 'ab_players':
                    return kpi(def, {
                        status: KPI_STATUS.NOT_MEASURED,
                        footer: def.source,
                    });
                case 'marge_per_loon':
                    if (margePerLoon != null) {
                        return kpi(def, {
                            status: mpl.status === KPI_STATUS.LIVE
                                ? KPI_STATUS.LIVE
                                : KPI_STATUS.IN_DEVELOPMENT,
                            value: margePerLoon,
                            delta: '',
                            footer: margeFooter,
                            note: mpl.totals
                                ? 'Rekening 8/6 + loonrekeningen (Brief Fonkel).'
                                : 'Wacht op Peliqan deploy marge_per_loon.',
                        });
                    }
                    return kpi(def, {
                        status: KPI_STATUS.IN_DEVELOPMENT,
                        footer: def.source,
                    });
                default:
                    return kpi(def);
            }
        });
    });

    const journeySections = computed(() =>
        CUSTOMER_JOURNEY_STAGES.map((stage) => ({
            ...stage,
            cards: stage.kpis.map((kpiId) => {
                const def = OPERATIONAL_KPIS[kpiId];
                return resolveOperational(def);
            }),
        })),
    );

    const tacticalCards = computed(() =>
        TACTICAL_KPIS.map((def) => resolveTactical(def)),
    );

    const entitySections = computed(() =>
        Object.values(ENTITY_KPIS).map((entity) => ({
            ...entity,
            cards: entity.kpis.map((def) => resolveEntityKpi(entity, def)),
        })),
    );

    function resolveOperational(def) {
        const dk = dealKpis.value;
        const tk = ticketKpis.value;
        const ss = sprinterSummary.value;
        const tl = tripleLob.value;
        const churnN = (hs.value?.churn_deals_proxy ?? []).length;
        const onboardingN = (hs.value?.onboarding_proxy ?? []).length;

        switch (def.id) {
            case 'icp_interactions':
                return kpi(def, {
                    status: KPI_STATUS.IN_DEVELOPMENT,
                    note: 'Proxy: deals/week. ICP-tag in HubSpot nog definiëren.',
                    footer: def.source,
                });
            case 'client_requests_lob':
                return kpi(def, {
                    status: KPI_STATUS.NOT_MEASURED,
                    footer: def.source,
                });
            case 'winrate': {
                const pipelines = dk.pipelines ?? [];
                if (pipelines.length === 1) {
                    const p = pipelines[0];
                    return kpi(def, {
                        status: KPI_STATUS.LIVE,
                        value:
                            p.winrate_pct != null
                                ? `${p.winrate_pct}%`
                                : '—',
                        delta:
                            p.prior?.winrate_pct != null &&
                            p.winrate_pct != null
                                ? deltaTxt(p.winrate_pct, p.prior.winrate_pct)
                                : '',
                        deltaPositive: deltaPositive(
                            p.winrate_pct,
                            p.prior?.winrate_pct,
                        ),
                        footer: `${p.gewonnen} gewonnen / ${p.gewonnen + p.verloren} gesloten · ${winratePeriodLabel.value}`,
                    });
                }
                if (pipelines.length > 1) {
                    const parts = pipelines
                        .filter((p) => p.winrate_pct != null)
                        .map((p) => `${p.pipeline_label}: ${p.winrate_pct}%`);
                    return kpi(def, {
                        status: KPI_STATUS.LIVE,
                        value: parts[0] ?? '—',
                        note: parts.slice(1).join(' · ') || null,
                        footer: `${winratePeriodLabel.value} · per pijplijn`,
                    });
                }
                if (dk.n > 0) {
                    return kpi(def, {
                        status: KPI_STATUS.IN_DEVELOPMENT,
                        value: `${dk.wr}%`,
                        footer: `${dk.won} gewonnen / ${dk.n} gesloten`,
                        note: 'Deploy Peliqan-handler voor winrate per pijplijn.',
                    });
                }
                return kpi(def, {
                    status: KPI_STATUS.NOT_MEASURED,
                    footer: def.source,
                });
            }
            case 'time_to_onboarding':
                return kpi(def, {
                    status:
                        onboardingN > 0
                            ? KPI_STATUS.IN_DEVELOPMENT
                            : KPI_STATUS.NOT_MEASURED,
                    note:
                        onboardingN > 0
                            ? `${onboardingN} gesloten deals in periode — geen gem. doorlooptijd`
                            : null,
                    footer: def.source,
                });
            case 'occupancy_rate': {
                if (wmsLoading.value) {
                    return kpi(def, {
                        status: KPI_STATUS.IN_DEVELOPMENT,
                        note: '7T WMS laden…',
                        footer: def.source,
                    });
                }
                const occ = occupancy.value;
                if (wmsAvailable.value && occ.rate != null) {
                    return kpi(def, {
                        status: KPI_STATUS.LIVE,
                        value: fmtPct(occ.rate),
                        footer: `${occ.occupied}/${occ.total} locaties · ${def.source}`,
                    });
                }
                return kpi(def, {
                    status: KPI_STATUS.NOT_MEASURED,
                    footer: wmsAvailable.value
                        ? def.source
                        : `${def.source} · niet bereikbaar`,
                });
            }
            case 'storage_lead_time': {
                if (wmsLoading.value) {
                    return kpi(def, {
                        status: KPI_STATUS.IN_DEVELOPMENT,
                        note: '7T WMS laden…',
                        footer: def.source,
                    });
                }
                const days = storageLeadTime.value;
                if (wmsAvailable.value && days != null) {
                    return kpi(def, {
                        status: KPI_STATUS.LIVE,
                        value: fmtDays(days),
                        footer: `Gem. leverdata · ${def.source}`,
                    });
                }
                return kpi(def, {
                    status: KPI_STATUS.NOT_MEASURED,
                    footer: wmsAvailable.value
                        ? def.source
                        : `${def.source} · niet bereikbaar`,
                });
            }
            case 'on_time_delivery':
                return kpi(def, {
                    status: KPI_STATUS.TO_DEFINE,
                    footer: def.source,
                });
            case 'churn':
                return kpi(def, {
                    status:
                        churnN > 0
                            ? KPI_STATUS.IN_DEVELOPMENT
                            : KPI_STATUS.NOT_MEASURED,
                    note:
                        churnN > 0
                            ? `Proxy: ${churnN} lost/€0 deals`
                            : null,
                    footer: def.source,
                });
            case 'tickets':
                if (tk.n > 0) {
                    return kpi(def, {
                        status: KPI_STATUS.LIVE,
                        value: String(tk.n),
                        delta: ticketsYoY.value
                            ? deltaTxt(tk.n, ticketsYoY.value)
                            : '',
                        deltaPositive: deltaPositive(
                            tk.n,
                            ticketsYoY.value,
                        ),
                        footer: `${tk.open} open · ${tk.closed} gesloten`,
                    });
                }
                return kpi(def, {
                    status: KPI_STATUS.NOT_MEASURED,
                    footer: def.source,
                });
            case 'margin_per_shipment':
                if (ss.n > 0 && ss.avgGpm != null) {
                    return kpi(def, {
                        status: KPI_STATUS.LIVE,
                        value: fmtEur(ss.avgGpm),
                        delta: deltaTxt(ss.gpm, ss.gpmYoY),
                        deltaPositive: deltaPositive(ss.gpm, ss.gpmYoY),
                        footer: `${ss.n} zendingen · totaal ${fmtEur(ss.gpm)}`,
                    });
                }
                return kpi(def, {
                    status: KPI_STATUS.NOT_MEASURED,
                    footer: def.source,
                });
            default:
                return kpi(def);
        }
    }

    function resolveTactical(def) {
        const tl = tripleLob.value;
        if (def.id === 'triple_lob_pct' && tl.nAll > 0) {
            return kpi(def, {
                status: KPI_STATUS.IN_DEVELOPMENT,
                note: `${tl.pctKlant}% klanten · ${tl.pctOmz}% omzet — validatie nodig`,
                footer: def.source,
            });
        }
        return kpi(def);
    }

    function resolveEntityKpi(entity, def) {
        const ss = sprinterSummary.value;
        const modes = sp.value?.shipment_modes ?? [];

        if (entity.code === 'AWC') {
            if (wmsLoading.value) {
                return kpi(def, {
                    status: KPI_STATUS.IN_DEVELOPMENT,
                    note: '7T WMS laden…',
                    footer: entity.source,
                });
            }
            switch (def.id) {
                case 'inventory_accuracy': {
                    const acc = inventoryAccuracy.value;
                    if (wmsAvailable.value && acc != null) {
                        return kpi(def, {
                            status: KPI_STATUS.LIVE,
                            value: fmtPct(acc),
                            footer: `Tellingen · ${entity.source}`,
                        });
                    }
                    break;
                }
                case 'throughput': {
                    const n = computeOntvangstenCount(wms.value);
                    const lookback = wms.value?.lookback_days ?? 180;
                    if (wmsAvailable.value && n > 0) {
                        return kpi(def, {
                            status: KPI_STATUS.IN_DEVELOPMENT,
                            value: String(n),
                            note: `Proxy: aantal ontvangsten (${lookback} dgn)`,
                            footer: entity.source,
                        });
                    }
                    break;
                }
            }
        }

        if (entity.code === 'AFC') {
            switch (def.id) {
                case 'shipments_afc':
                    if (ss.n > 0) {
                        return kpi(def, {
                            status: KPI_STATUS.LIVE,
                            value: String(ss.n),
                            delta: deltaTxt(ss.n, ss.nYoY),
                            deltaPositive: deltaPositive(ss.n, ss.nYoY),
                            footer: entity.source,
                        });
                    }
                    break;
                case 'modal_split':
                    if (modes.length > 0) {
                        const top = modes[0];
                        return kpi(def, {
                            status: KPI_STATUS.LIVE,
                            value: String(top.shipment_mode ?? '—'),
                            note: modes
                                .slice(0, 3)
                                .map(
                                    (m) =>
                                        `${m.shipment_mode}: ${m.n}`,
                                )
                                .join(' · '),
                            footer: entity.source,
                        });
                    }
                    break;
                case 'margin_per_modality':
                    if (modes.length > 0) {
                        const best = [...modes].sort(
                            (a, b) =>
                                Number(b.gem_gpm ?? 0) -
                                Number(a.gem_gpm ?? 0),
                        )[0];
                        return kpi(def, {
                            status: KPI_STATUS.LIVE,
                            value: fmtEur(best?.gem_gpm),
                            note: `Hoogste gem. GPM: ${best?.shipment_mode}`,
                            footer: entity.source,
                        });
                    }
                    break;
            }
        }

        return kpi({
            ...def,
            source: entity.source,
        });
    }

    function fmtEurDisplay(n) {
        return fmtEur(n) ?? '—';
    }

    function adminOmzetMaps(data) {
        const omzet = {};
        const omzetV = {};
        const inkoop = {};
        const inkoopV = {};
        for (const r of data?.omzet_detail ?? []) {
            const code = r.admin_code ?? '—';
            omzet[code] = (omzet[code] || 0) + Number(r.debet ?? 0);
        }
        for (const r of data?.omzet_vorig_per_admin ?? []) {
            omzetV[r.admin_code ?? '—'] = Number(r.debet_v ?? 0);
        }
        for (const r of data?.inkoop_per_admin ?? []) {
            const code = r.admin_code ?? '—';
            inkoop[code] = Math.abs(Number(r.credit_ink ?? 0));
        }
        for (const r of data?.inkoop_vorig_per_admin ?? []) {
            inkoopV[r.admin_code ?? '—'] = Math.abs(Number(r.credit_ink ?? 0));
        }
        return { omzet, omzetV, inkoop, inkoopV };
    }

    /** Financiële bouwstenen — alleen detail-tab, niet strategische kop */
    const financeDetail = computed(() => {
        const a = aggregates.value;
        if (!a) return [];
        const period = applied.value?.book_periods ?? '';
        return [
            {
                id: 'omzet',
                title: 'Omzet (detail)',
                value: fmtEur(a.omzet),
                delta: deltaTxt(a.omzet, a.omzet_vorig),
                deltaPositive: deltaPositive(a.omzet, a.omzet_vorig),
                footer: `Cashweb · ${period}`,
                calculation:
                    'Som debet (D-kant), dagboeken 50 en VERK.',
            },
            {
                id: 'inkoop',
                title: 'Inkoopkosten',
                value: fmtEur(a.inkoop),
                delta: deltaTxt(a.inkoop, a.inkoop_vorig),
                deltaPositive: !deltaPositive(a.inkoop, a.inkoop_vorig),
                footer: 'Dagboek INK',
                calculation: 'Som credit, dagboek INK.',
            },
            {
                id: 'brutomarge',
                title: 'Brutomarge',
                value: fmtEur(a.brutomarge),
                delta: deltaTxt(a.brutomarge, a.brutomarge_vorig),
                deltaPositive: deltaPositive(a.brutomarge, a.brutomarge_vorig),
                footer: 'Omzet − inkoop',
                calculation: 'Omzet minus inkoopkosten, per admin.',
            },
            {
                id: 'marge_pct',
                title: 'Marge %',
                value: `${Number(a.marge_pct ?? 0).toFixed(1)}%`,
                delta: a.brutomarge_vorig && a.omzet_vorig
                    ? deltaTxt(
                          a.marge_pct,
                          (a.brutomarge_vorig / a.omzet_vorig) * 100,
                      )
                    : '',
                deltaPositive: true,
                footer: 'Brutomarge / omzet',
                calculation: 'Brutomarge gedeeld door omzet, per admin.',
            },
        ];
    });

    const financeDrawerRows = computed(() => {
        const data = cw.value;
        if (!data) {
            return { omzet: [], inkoop: [], brutomarge: [], marge_pct: [] };
        }
        const { omzet, omzetV, inkoop, inkoopV } = adminOmzetMaps(data);

        const omzetRows = (data.omzet_detail ?? [])
            .map((r) => ({
                admin_code: r.admin_code ?? '—',
                sub_administration: r.sub_administration ?? '—',
                journal_code: r.journal_code ?? '—',
                debet: Number(r.debet ?? 0),
                debet_fmt: fmtEurDisplay(r.debet),
                credit: Number(r.credit ?? 0),
                credit_fmt: fmtEurDisplay(r.credit),
                mutaties: Number(r.mutaties ?? 0),
            }))
            .sort((a, b) => b.debet - a.debet);

        const inkoopRows = (data.inkoop_per_admin ?? [])
            .map((r) => {
                const code = r.admin_code ?? '—';
                const cur = Math.abs(Number(r.credit_ink ?? 0));
                const prev = inkoopV[code] ?? 0;
                return {
                    admin_code: code,
                    inkoop: cur,
                    inkoop_fmt: fmtEurDisplay(cur),
                    mutaties: Number(r.mutaties ?? 0),
                    inkoop_vorig_fmt: prev ? fmtEurDisplay(prev) : '—',
                    delta: deltaTxt(cur, prev),
                };
            })
            .sort((a, b) => b.inkoop - a.inkoop);

        const adminCodes = new Set([
            ...Object.keys(omzet),
            ...Object.keys(inkoop),
        ]);
        const marginRows = [...adminCodes]
            .map((admin_code) => {
                const o = omzet[admin_code] ?? 0;
                const i = inkoop[admin_code] ?? 0;
                const marge = o - i;
                const margeV =
                    (omzetV[admin_code] ?? 0) - (inkoopV[admin_code] ?? 0);
                const pct = o > 0 ? (marge / o) * 100 : null;
                const pctV =
                    (omzetV[admin_code] ?? 0) > 0
                        ? (margeV / omzetV[admin_code]) * 100
                        : null;
                return {
                    admin_code,
                    omzet: o,
                    omzet_fmt: fmtEurDisplay(o),
                    inkoop: i,
                    inkoop_fmt: fmtEurDisplay(i),
                    brutomarge: marge,
                    brutomarge_fmt: fmtEurDisplay(marge),
                    marge_pct:
                        pct != null ? `${pct.toFixed(1)}%` : '—',
                    marge_pct_num: pct ?? 0,
                    delta_marge: deltaTxt(marge, margeV),
                    delta_pct: pct != null ? deltaTxt(pct, pctV) : '',
                };
            })
            .sort((a, b) => b.brutomarge - a.brutomarge);

        return {
            omzet: omzetRows,
            inkoop: inkoopRows,
            brutomarge: marginRows,
            marge_pct: [...marginRows].sort(
                (a, b) => b.marge_pct_num - a.marge_pct_num,
            ),
        };
    });

    const financePeriodLabel = computed(() => {
        const f = applied.value;
        if (!f) return '';
        const parts = [f.book_year, f.book_periods].filter(Boolean);
        return parts.join(' · ');
    });

    return {
        strategicCards,
        journeySections,
        tacticalCards,
        entitySections,
        financeDetail,
        financeDrawerRows,
        financePeriodLabel,
        revenuePerLobPanel,
        winratePipelines,
        winratePeriodLabel,
        margePerLoonPanel,
        wmsAvailable,
        occupancy,
        storageLeadTime,
    };
}

export const FINANCE_DRAWER_COLUMNS = {
    omzet: [
        { field: 'admin_code', header: 'Admin' },
        { field: 'sub_administration', header: 'Sub-admin' },
        { field: 'journal_code', header: 'Dagboek' },
        { field: 'debet_fmt', header: 'Debet' },
        { field: 'credit_fmt', header: 'Credit' },
        { field: 'mutaties', header: '# Mutaties' },
    ],
    inkoop: [
        { field: 'admin_code', header: 'Admin' },
        { field: 'inkoop_fmt', header: 'Inkoop' },
        { field: 'inkoop_vorig_fmt', header: 'Vorig jaar' },
        { field: 'delta', header: 'Δ%' },
        { field: 'mutaties', header: '# Mutaties' },
    ],
    brutomarge: [
        { field: 'admin_code', header: 'Admin' },
        { field: 'omzet_fmt', header: 'Omzet' },
        { field: 'inkoop_fmt', header: 'Inkoop' },
        { field: 'brutomarge_fmt', header: 'Brutomarge' },
        { field: 'delta_marge', header: 'Δ%' },
    ],
    marge_pct: [
        { field: 'admin_code', header: 'Admin' },
        { field: 'brutomarge_fmt', header: 'Brutomarge' },
        { field: 'omzet_fmt', header: 'Omzet' },
        { field: 'marge_pct', header: 'Marge %' },
        { field: 'delta_pct', header: 'Δ%' },
    ],
};
