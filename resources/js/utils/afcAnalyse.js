/**
 * Rekenwerk voor de AFC-analyse. Alle functies zijn puur: ze krijgen rijen uit de
 * kpi_afc_*-views (zie documentation/AFC-analyse.md) en geven tabellen/reeksen terug.
 */

export const AFC_VIEWS = [
    'kpi_afc_zending_maand',
    'kpi_afc_eigenaar_maand',
    'kpi_afc_klant_jaar',
    'kpi_afc_klant',
    'kpi_afc_klant_retentie_jaar',
    'kpi_afc_resultaat_maand',
];

export const MODALITEITEN = ['Weg', 'Zee', 'Lucht'];
export const RICHTINGEN = ['Export', 'Import', 'Domestic'];
export const KLANTSTATUSSEN = ['Actief', 'Nieuw', 'Dalend', 'Verloren', 'Eenmalig'];

export const MAANDEN_KORT = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];

const num = (v) => (v == null || v === '' ? 0 : Number(v));
const truthy = (v) => v === true || v === 'true' || v === 1 || v === 't';

export function maandVan(row) {
    return Number(String(row.maand ?? '').slice(5, 7)) || Number(row.maandnummer) || 0;
}

export function pct(deel, geheel) {
    return geheel ? (100 * deel) / geheel : null;
}

export function groei(nu, vorig) {
    return vorig ? (100 * (nu - vorig)) / Math.abs(vorig) : null;
}

/** Som van zendingen/omzet/marge over rijen. */
export function som(rows) {
    return rows.reduce(
        (acc, r) => {
            acc.zendingen += num(r.zendingen);
            acc.omzet += num(r.omzet);
            acc.marge += num(r.marge);
            acc.omzetInclRechten += num(r.omzet_incl_invoerrechten);
            acc.open += num(r.zendingen_open);

            return acc;
        },
        { zendingen: 0, omzet: 0, marge: 0, omzetInclRechten: 0, open: 0 },
    );
}

export function filterRichting(rows, richting) {
    return richting === 'alle' ? rows : rows.filter((r) => r.richting === richting);
}

export function ytdRows(rows, jaar) {
    return rows.filter((r) => Number(r.jaar) === jaar && truthy(r.ytd_venster));
}

/** Kerncijfers: jaar t/m vandaag tegen dezelfde periode vorig jaar, plus laatste volle maand. */
export function kerncijfers(zendingRows, jaar, laatsteVolleMaand) {
    const nu = som(ytdRows(zendingRows, jaar));
    const vorig = som(ytdRows(zendingRows, jaar - 1));
    const maand = (j, m) =>
        som(zendingRows.filter((r) => Number(r.jaar) === j && maandVan(r) === m));
    const m = laatsteVolleMaand;
    const maandNu = m ? maand(jaar, m) : null;
    const maandVorig = m ? (m > 1 ? maand(jaar, m - 1) : maand(jaar - 1, 12)) : null;

    return { nu, vorig, maand: m, maandNu, maandVorig };
}

/** Per modaliteit, jaar t/m vandaag naast dezelfde periode vorig jaar. */
export function perModaliteit(zendingRows, jaar) {
    const rows = MODALITEITEN.map((mod) => {
        const nu = som(ytdRows(zendingRows, jaar).filter((r) => r.modaliteit === mod));
        const vorig = som(ytdRows(zendingRows, jaar - 1).filter((r) => r.modaliteit === mod));

        return { modaliteit: mod, nu, vorig };
    }).filter((r) => r.nu.zendingen || r.vorig.zendingen);

    const totaal = {
        modaliteit: 'Totaal',
        nu: som(ytdRows(zendingRows, jaar)),
        vorig: som(ytdRows(zendingRows, jaar - 1)),
    };

    return [...rows, totaal].map((r) => ({
        modaliteit: r.modaliteit,
        zendingen: r.nu.zendingen,
        omzet: r.nu.omzet,
        marge: r.nu.marge,
        margePct: pct(r.nu.marge, r.nu.omzet),
        omzetVorig: r.vorig.omzet,
        margeVorig: r.vorig.marge,
        margePctVorig: pct(r.vorig.marge, r.vorig.omzet),
        groeiOmzet: groei(r.nu.omzet, r.vorig.omzet),
        groeiMarge: groei(r.nu.marge, r.vorig.marge),
        isTotaal: r.modaliteit === 'Totaal',
    }));
}

/** Reeksen per maand en modaliteit (gestapelde staven). */
export function maandModaliteitReeks(zendingRows, maat) {
    const veld = { omzet: 'omzet', marge: 'marge', zendingen: 'zendingen' }[maat] ?? 'omzet';
    const maanden = [...new Set(zendingRows.map((r) => String(r.maand).slice(0, 10)))].sort();
    const series = MODALITEITEN.map((mod) => ({
        modaliteit: mod,
        data: maanden.map((m) =>
            zendingRows
                .filter((r) => String(r.maand).slice(0, 10) === m && r.modaliteit === mod)
                .reduce((s, r) => s + num(r[veld]), 0),
        ),
    }));

    return { maanden, series };
}

/** Resultaat volgens Cash per boekjaar, t/m maand M. */
export function resultaatPerJaar(resultaatRows, tmMaand) {
    const jaren = [...new Set(resultaatRows.map((r) => Number(r.boekjaar)))].sort();
    const perJaar = jaren.map((jaar) => {
        const rows = resultaatRows.filter(
            (r) => Number(r.boekjaar) === jaar && Number(r.maandnummer) <= tmMaand,
        );
        const s = (veld) => rows.reduce((acc, r) => acc + num(r[veld]), 0);
        const omzet = s('omzet');
        const kostprijs = s('kostprijs');

        return {
            jaar,
            omzet,
            kostprijs,
            brutomarge: s('brutomarge'),
            brutomargePct: pct(s('brutomarge'), omzet),
            bedrijfskosten: s('bedrijfskosten'),
            overig: s('resultaat_humber'),
            resultaat: s('resultaat_voor_belasting'),
            afwijkend: s('periode_afwijkend'),
        };
    });

    return perJaar.map((r, i) => {
        const vorig = perJaar[i - 1];

        return {
            ...r,
            groeiOmzet: vorig ? groei(r.omzet, vorig.omzet) : null,
            resultaatVerschil: vorig ? r.resultaat - vorig.resultaat : null,
        };
    });
}

/** Cumulatief per maand per boekjaar, voor de lijngrafiek. Lopend jaar stopt na t/m-maand. */
export function cumulatiefPerJaar(resultaatRows, veld, lopendJaar, tmMaand) {
    const jaren = [...new Set(resultaatRows.map((r) => Number(r.boekjaar)))].sort();

    return jaren.map((jaar) => {
        let totaal = 0;
        const data = Array.from({ length: 12 }, (_, i) => {
            const mnd = i + 1;
            if (jaar === lopendJaar && mnd > tmMaand) {
                return null;
            }
            const row = resultaatRows.find(
                (r) => Number(r.boekjaar) === jaar && Number(r.maandnummer) === mnd,
            );
            totaal += num(row?.[veld]);

            return Math.round(totaal);
        });

        return { jaar, data };
    });
}

/**
 * Top klanten (klantgroep) voor het gekozen jaar t/m vandaag.
 * @returns {{ rows: object[], totaalMarge: number, top2Aandeel: number|null }}
 */
export function topKlanten(klantJaarRows, jaar, { richting = 'alle', modaliteit = 'alle', limiet = 40 } = {}) {
    let rows = filterRichting(klantJaarRows, richting);
    if (modaliteit !== 'alle') {
        rows = rows.filter((r) => r.modaliteit === modaliteit);
    }
    const groepen = new Map();
    const pak = (id, r) => {
        if (!groepen.has(id)) {
            groepen.set(id, {
                klantgroepId: id,
                klant: r.klant,
                debiteurnummer: r.debiteurnummer,
                modaliteiten: new Set(),
                richtingen: new Set(),
                zendingen: 0,
                omzet: 0,
                marge: 0,
                omzetVorig: 0,
                margeVorig: 0,
            });
        }

        return groepen.get(id);
    };

    for (const r of ytdRows(rows, jaar)) {
        const g = pak(r.klantgroep_id, r);
        g.modaliteiten.add(r.modaliteit);
        g.richtingen.add(r.richting);
        g.zendingen += num(r.zendingen);
        g.omzet += num(r.omzet);
        g.marge += num(r.marge);
    }
    for (const r of ytdRows(rows, jaar - 1)) {
        if (groepen.has(r.klantgroep_id)) {
            const g = groepen.get(r.klantgroep_id);
            g.omzetVorig += num(r.omzet);
            g.margeVorig += num(r.marge);
        }
    }

    const alle = [...groepen.values()];
    const totaalMarge = alle.reduce((s, g) => s + g.marge, 0);
    const gesorteerd = alle.sort((a, b) => b.omzet - a.omzet);
    const opMarge = [...alle].sort((a, b) => b.marge - a.marge);
    const top2Aandeel = totaalMarge
        ? pct(opMarge.slice(0, 2).reduce((s, g) => s + g.marge, 0), totaalMarge)
        : null;

    return {
        rows: gesorteerd.slice(0, limiet).map((g) => ({
            ...g,
            naam: g.debiteurnummer ? `${g.klant} (${g.debiteurnummer})` : `${g.klant} (geen debiteur)`,
            modaliteiten: [...g.modaliteiten].join(', '),
            richtingen: [...g.richtingen].join(', '),
            margePct: pct(g.marge, g.omzet),
            aandeelMarge: pct(g.marge, totaalMarge),
        })),
        totaalMarge,
        top2Aandeel,
        aantal: alle.length,
    };
}

/** Klantstatus nu: aantallen en omzet per status. */
export function statusOverzicht(klantRows) {
    return KLANTSTATUSSEN.map((status) => {
        const rows = klantRows.filter((r) => r.klantstatus === status);

        return {
            status,
            klanten: rows.length,
            omzetVorig12m: rows.reduce((s, r) => s + num(r.omzet_vorige_12m), 0),
            omzet12m: rows.reduce((s, r) => s + num(r.omzet_12m), 0),
        };
    });
}

export function klantenMetStatus(klantRows, status, limiet = 50) {
    const sortVeld = status === 'Verloren' || status === 'Dalend' || status === 'Eenmalig'
        ? 'omzet_vorige_12m'
        : 'omzet_12m';

    return klantRows
        .filter((r) => r.klantstatus === status)
        .sort((a, b) => num(b[sortVeld]) - num(a[sortVeld]))
        .slice(0, limiet);
}

/** Per dossiereigenaar, gekozen jaar t/m vandaag. */
export function perEigenaar(eigenaarRows, jaar) {
    const groepen = new Map();
    for (const r of ytdRows(eigenaarRows, jaar)) {
        const naam = r.eigenaar ?? '(onbekend)';
        if (!groepen.has(naam)) {
            groepen.set(naam, { eigenaar: naam, zendingen: 0, omzet: 0, marge: 0, zonderAfdeling: 0 });
        }
        const g = groepen.get(naam);
        g.zendingen += num(r.zendingen);
        g.omzet += num(r.omzet);
        g.marge += num(r.marge);
        if (!r.afdeling || r.afdeling === '(geen)') {
            g.zonderAfdeling += num(r.zendingen);
        }
    }

    return [...groepen.values()]
        .map((g) => ({ ...g, margePct: pct(g.marge, g.omzet) }))
        .sort((a, b) => b.omzet - a.omzet);
}

/** Aansluiting Sprinter (rapportagedatum) met Cash (boekperiode), per maand van het jaar. */
export function aansluiting(zendingRows, resultaatRows, jaar) {
    return Array.from({ length: 12 }, (_, i) => {
        const mnd = i + 1;
        const sprinter = som(zendingRows.filter((r) => Number(r.jaar) === jaar && maandVan(r) === mnd));
        const cash = resultaatRows.find(
            (r) => Number(r.boekjaar) === jaar && Number(r.maandnummer) === mnd,
        );

        return {
            maand: mnd,
            omzetSprinter: sprinter.omzetInclRechten,
            omzetCash: num(cash?.omzet),
            margeSprinter: sprinter.marge,
            margeCash: num(cash?.brutomarge),
            kostprijsCash: num(cash?.kostprijs),
            invoerrechten: num(cash?.invoerrechten_doorbelast),
            simCargo: num(cash?.kostprijs_sim_cargo),
            heeftData: sprinter.zendingen > 0 || cash != null,
        };
    }).filter((r) => r.heeftData);
}

/** Sim Cargo en SVZ per boekjaar. */
export function ketenPerJaar(resultaatRows) {
    const jaren = [...new Set(resultaatRows.map((r) => Number(r.boekjaar)))].sort();

    return jaren.map((jaar) => {
        const rows = resultaatRows.filter((r) => Number(r.boekjaar) === jaar && num(r.kostprijs) !== 0);
        const simCargo = rows.reduce((s, r) => s + num(r.kostprijs_sim_cargo), 0);
        const svz = rows.reduce((s, r) => s + num(r.kostprijs_svz), 0);
        const kostprijs = rows.reduce((s, r) => s + num(r.kostprijs), 0);

        return {
            jaar,
            simCargo,
            svz,
            samen: simCargo + svz,
            kostprijs,
            aandeel: pct(simCargo + svz, kostprijs),
            maanden: rows.length,
        };
    });
}
