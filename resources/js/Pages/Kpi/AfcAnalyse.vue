<script setup>
import AfcFinancieel from '@/Components/Kpi/AfcAnalyse/AfcFinancieel.vue';
import AfcEigenaren from '@/Components/Kpi/AfcAnalyse/AfcEigenaren.vue';
import AfcInfo from '@/Components/Kpi/KpiInfo.vue';
import AfcKaart from '@/Components/Kpi/AfcAnalyse/AfcKaart.vue';
import AfcKeuze from '@/Components/Kpi/AfcAnalyse/AfcKeuze.vue';
import AfcKlantbehoud from '@/Components/Kpi/AfcAnalyse/AfcKlantbehoud.vue';
import AfcKlanten from '@/Components/Kpi/AfcAnalyse/AfcKlanten.vue';
import AfcModaliteit from '@/Components/Kpi/AfcAnalyse/AfcModaliteit.vue';
import AfcResultaatCash from '@/Components/Kpi/AfcAnalyse/AfcResultaatCash.vue';
import AfcSegment from '@/Components/Kpi/AfcAnalyse/AfcSegment.vue';
import KpiFeedbackWidget from '@/Components/Kpi/KpiFeedbackWidget.vue';
import KpiScreenHeader from '@/Components/Kpi/KpiScreenHeader.vue';
import KpiScreenNav from '@/Components/Kpi/KpiScreenNav.vue';
import { fetchKpiDrill } from '@/composables/useKpiDrillFetch';
import KpiStandaloneLayout from '@/Layouts/KpiStandaloneLayout.vue';
import {
    AFC_VIEWS,
    MAANDEN_KORT,
    filterRichting,
    groei,
    kerncijfers,
    pct,
    topKlanten,
} from '@/utils/afcAnalyse';
import { euroKort, getal, groeiKlasse, groeiTekst, procent } from '@/utils/afcFormat';
import { Head, Link } from '@inertiajs/vue3';
import Message from 'primevue/message';
import ProgressSpinner from 'primevue/progressspinner';
import { computed, onMounted, ref } from 'vue';

const props = defineProps({
    peliqanError: { type: String, default: null },
    kpiUsesFixture: { type: Boolean, default: false },
    vandaag: { type: String, required: true },
});

const loading = ref(true);
const error = ref(null);
const tables = ref({});
const controles = ref({ fout: 0, let_op: 0, ok: 0 });

async function laadControles() {
    try {
        const res = await fetch(route('kpi.api.controles'), {
            headers: { Accept: 'application/json' },
            credentials: 'same-origin',
        });
        const json = await res.json();
        if (res.ok && json.controles_summary) {
            controles.value = json.controles_summary;
        }
    } catch {
        // De teller in de kop is bijzaak; de pagina werkt zonder.
    }
}

onMounted(async () => {
    laadControles();
    const { tables: t, error: err } = await fetchKpiDrill(AFC_VIEWS, { limit: 5000 });
    tables.value = t;
    error.value = err;
    loading.value = false;
});

const rows = (view) => tables.value[view] ?? [];

const [vandaagJaar, vandaagMaand, vandaagDag] = props.vandaag.split('-').map(Number);

const jaren = computed(() =>
    [...new Set(rows('kpi_afc_zending_maand').map((r) => Number(r.jaar)))].sort((a, b) => b - a),
);
const jaar = ref(vandaagJaar);
const jaarOpties = computed(() => jaren.value.map((j) => ({ value: j, label: String(j) })));

const richting = ref('alle');
const richtingOpties = [
    { value: 'alle', label: 'Alle' },
    { value: 'Export', label: 'Export' },
    { value: 'Import', label: 'Import' },
    { value: 'Domestic', label: 'Binnenland' },
];

/** Laatste volle maand: in het lopende jaar de maand vóór vandaag, in eerdere jaren december. */
const laatsteVolleMaand = computed(() =>
    jaar.value === vandaagJaar ? Math.max(vandaagMaand - 1, 0) : 12,
);

const zendingen = computed(() => filterRichting(rows('kpi_afc_zending_maand'), richting.value));

const kern = computed(() => kerncijfers(zendingen.value, jaar.value, laatsteVolleMaand.value));

/** Jaren waarvoor klant- en eigenaarcijfers bestaan (de views houden lopend en vorig jaar bij). */
const klantJaren = computed(() =>
    [...new Set(rows('kpi_afc_klant_jaar').map((r) => Number(r.jaar)))].sort((a, b) => b - a),
);
const eigenaarJaren = computed(() =>
    [...new Set(rows('kpi_afc_eigenaar_maand').map((r) => Number(r.jaar)))].sort((a, b) => b - a),
);

const top2 = computed(() =>
    klantJaren.value.includes(jaar.value)
        ? topKlanten(rows('kpi_afc_klant_jaar'), jaar.value, { richting: richting.value }).top2Aandeel
        : null,
);

const tmLabel = `${String(vandaagDag).padStart(2, '0')}-${String(vandaagMaand).padStart(2, '0')}`;

const samenvatting = computed(() => {
    const { nu, vorig } = kern.value;
    if (!nu.zendingen) {
        return null;
    }
    const g = groei(nu.omzet, vorig.omzet);
    const delen = [
        `${jaar.value} t/m ${tmLabel}: omzet ${euroKort(nu.omzet)}`,
        g != null ? ` (${groeiTekst(g)} t.o.v. dezelfde periode vorig jaar)` : '',
        `, brutomarge ${euroKort(nu.marge)} (${procent(pct(nu.marge, nu.omzet))} van de omzet).`,
        top2.value != null ? ` De twee grootste klanten leveren ${procent(top2.value)} van de marge.` : '',
    ];

    return delen.join('');
});

const maandNaam = (m) => (m ? MAANDEN_KORT[m - 1] : '');

const kaarten = computed(() => {
    const { nu, vorig, maand, maandNu, maandVorig } = kern.value;
    const vorigeMaandNaam = maand ? maandNaam(maand > 1 ? maand - 1 : 12) : '';
    const maandRegel = (fmt, veld) =>
        maand && maandNu
            ? `${maandNaam(maand)}: ${fmt(maandNu[veld])} (${vorigeMaandNaam} ${fmt(maandVorig?.[veld])})`
            : null;
    const margePctNu = pct(nu.marge, nu.omzet);
    const margePctVorig = pct(vorig.marge, vorig.omzet);

    return [
        {
            label: 'Omzet, jaar t/m vandaag',
            waarde: euroKort(nu.omzet),
            groei: groei(nu.omzet, vorig.omzet),
            regel2: maandRegel(euroKort, 'omzet'),
        },
        {
            label: 'Brutomarge, jaar t/m vandaag',
            waarde: euroKort(nu.marge),
            groei: groei(nu.marge, vorig.marge),
            regel2: maandRegel(euroKort, 'marge'),
        },
        {
            label: 'Marge in % van omzet',
            waarde: procent(margePctNu),
            sub: margePctVorig != null ? `vorig jaar ${procent(margePctVorig)}` : null,
            regel2:
                maand && maandNu
                    ? `${maandNaam(maand)}: ${procent(pct(maandNu.marge, maandNu.omzet))}`
                    : null,
        },
        {
            label: 'Zendingen',
            waarde: getal(nu.zendingen),
            groei: groei(nu.zendingen, vorig.zendingen),
            regel2: maandRegel(getal, 'zendingen'),
        },
    ];
});

const openZendingen = computed(() =>
    kern.value.maandNu ? kern.value.maandNu.open : 0,
);

const loadError = computed(() => props.peliqanError ?? error.value);
const heeftData = computed(() => rows('kpi_afc_zending_maand').length > 0);
</script>

<template>
    <Head title="AFC-analyse" />

    <KpiStandaloneLayout>
        <div class="min-h-full bg-awc-platinum">
            <KpiScreenHeader
                scherm="afc"
                :bijgewerkt-label="vandaag.split('-').reverse().join('-')"
                :controles="controles"
                :fixture="kpiUsesFixture"
            />
            <KpiScreenNav scherm="afc" />

            <div class="mx-auto max-w-[1440px] space-y-6 px-4 pb-24 pt-6 lg:px-8">
                <div>
                    <Link
                        :href="route('kpi.screen', { scherm: 'afc' })"
                        class="text-xs text-gray-600 underline-offset-2 hover:text-gray-900 hover:underline"
                    >
                        ‹ Terug naar AFC Freight
                    </Link>
                    <h1 class="mt-2 flex items-center gap-2 text-xl font-semibold text-gray-900">
                        AFC-analyse
                        <AfcInfo
                            :tekst="[
                                'Sprinter (zendingen) naast Cash (grootboek van Amsterdam Freight Company).',
                                'Marge is de brutomarge volgens Sprinter: verkoop min gereserveerde inkoop. Omzet overal excl. invoerrechten en btw.',
                                'Het richtingfilter werkt op alle Sprinter-cijfers; Cash en klantstatus kennen geen richting.',
                            ]"
                        />
                    </h1>
                </div>

                <div
                    class="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-md border border-gray-200 bg-white px-3 py-2 shadow-sm"
                >
                    <AfcKeuze v-model="jaar" label="Jaar" :opties="jaarOpties" />
                    <AfcSegment v-model="richting" label="Richting" :opties="richtingOpties" />
                </div>

                <Message v-if="loadError" severity="warn" class="w-full">{{ loadError }}</Message>

                <div v-if="loading" class="flex justify-center py-16">
                    <ProgressSpinner style="width: 2.5rem; height: 2.5rem" />
                </div>

                <template v-else-if="heeftData">
                    <section>
                        <p v-if="samenvatting" class="max-w-4xl text-base leading-relaxed text-gray-900">
                            {{ samenvatting }}
                        </p>
                        <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                            <AfcKaart
                                v-for="k in kaarten"
                                :key="k.label"
                                :label="k.label"
                                :waarde="k.waarde"
                                :sub="k.sub ?? (k.groei != null ? `${groeiTekst(k.groei)} t.o.v. vorig jaar` : null)"
                                :sub-klasse="k.sub ? 'text-gray-500' : groeiKlasse(k.groei)"
                                :regel2="k.regel2"
                            />
                        </div>
                        <p class="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                            <span class="inline-flex items-center gap-1">
                                Hoe lees ik dit
                                <AfcInfo tekst="Jaar t/m vandaag tegen dezelfde kalenderperiode een jaar eerder, op rapportagedatum. De tweede regel is de laatste volle maand naast de maand ervoor." />
                            </span>
                            <span
                                v-if="openZendingen"
                                class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-800 ring-1 ring-amber-200"
                            >
                                {{ getal(openZendingen) }} open in {{ maandNaam(kern.maand) }}
                                <AfcInfo tekst="Deze zendingen zijn nog niet gefactureerd; hun marge kan nog veranderen." />
                            </span>
                        </p>
                    </section>

                    <AfcResultaatCash
                        :rows="rows('kpi_afc_resultaat_maand')"
                        :lopend-jaar="jaar"
                        :laatste-volle-maand="laatsteVolleMaand"
                    />

                    <AfcModaliteit :rows="zendingen" :jaar="jaar" />

                    <AfcKlanten
                        :rows="rows('kpi_afc_klant_jaar')"
                        :jaar="jaar"
                        :richting="richting"
                        :beschikbare-jaren="klantJaren"
                    />

                    <AfcKlantbehoud
                        :klanten="rows('kpi_afc_klant')"
                        :retentie="rows('kpi_afc_klant_retentie_jaar')"
                    />

                    <AfcEigenaren
                        :rows="filterRichting(rows('kpi_afc_eigenaar_maand'), richting)"
                        :jaar="jaar"
                        :beschikbare-jaren="eigenaarJaren"
                    />

                    <AfcFinancieel
                        :zending-rows="rows('kpi_afc_zending_maand')"
                        :resultaat-rows="rows('kpi_afc_resultaat_maand')"
                        :jaar="jaar"
                    />

                    <details class="rounded-xl border border-gray-200 bg-white p-5 text-sm text-gray-600 lg:p-6">
                        <summary class="cursor-pointer font-semibold text-gray-900">Definities</summary>
                        <ul class="mt-3 max-w-3xl list-disc space-y-1.5 pl-5 leading-relaxed">
                            <li>Bron Sprinter: de koppeling sprinter_api in Peliqan (zendingen vanaf maart 2023). Geannuleerde zendingen (status C) tellen niet mee.</li>
                            <li>Omzet en marge in Sprinter zijn totalen per zending. De inkoop is de reservering in Sprinter, niet de definitieve inkoopfactuur. Open zendingen (status O) kunnen nog veranderen.</li>
                            <li>Omzet excl. invoerrechten en btw: Sprinter-omzet min de doorbelaste invoerrechten uit Cash (rekening 2001), gekoppeld via het zendingnummer. Zendingen die (nog) niet in Cash staan, tonen de Sprinter-omzet zoals die is.</li>
                            <li>Klantstatus en omzet per klant over 12 maanden komen uit de klanttabel en zijn incl. invoerrechten. De status geldt per Sprinter-klant, niet per samengevoegde klantgroep.</li>
                            <li>Cash: administratie pgl1 (AFC). Omzet = rekeningen 8xxx, kostprijs = 6xxx, bedrijfskosten = 4xxx. Boekingen die de koppeling dubbel binnenhaalt, tellen één keer.</li>
                            <li>De maandmarge in Cash schommelt sterk, omdat inkoopfacturen later worden geboekt dan verkoopfacturen. Kijk daarom naar meerdere maanden samen.</li>
                            <li>Richting volgens Sprinter: Export, Import en Binnenland (Domestic).</li>
                        </ul>
                    </details>
                </template>

                <p v-else-if="!loadError" class="text-sm text-gray-600">Nog geen AFC-gegevens beschikbaar.</p>
            </div>
        </div>

        <KpiFeedbackWidget scherm="afc" entiteit="concern" />
    </KpiStandaloneLayout>
</template>
