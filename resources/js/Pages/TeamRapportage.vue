<script setup>
import RapportageKpiCard from '@/Components/Management/RapportageKpiCard.vue';
import ManagementLayout from '@/Layouts/ManagementLayout.vue';
import { Head } from '@inertiajs/vue3';
import { computed, ref } from 'vue';
import Card from 'primevue/card';
import DatePicker from 'primevue/datepicker';
import MultiSelect from 'primevue/multiselect';

const props = defineProps({
    teamCode: {
        type: String,
        required: true,
        validator: (v) => ['AWC', 'AFC', 'ACC'].includes(v),
    },
});

const filterLabel =
    'mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-500';
const sectionOrange =
    'text-xs font-semibold uppercase tracking-wider text-[#ff7020]';

const companyOptions = ['Bedrijf A', 'Bedrijf B', 'Bedrijf C'];

const startDate = ref(new Date(2026, 0, 1));
const endDate = ref(new Date(2026, 0, 31));
const companies = ref(['Bedrijf A', 'Bedrijf B']);

function formatNl(d) {
    if (!d || !(d instanceof Date)) return '';
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
}

const heroDatum = computed(() => formatNl(startDate.value));

const pageTitle = computed(
    () => `Dashboard Rapportage · ${props.teamCode}`,
);

const sharedKpis = computed(() => [
    {
        title: 'Bruto marge per FTE',
        placeholder: true,
    },
    {
        title: 'Intern vs. Extern',
        value: '78%',
        sublabel: 'stabiel',
        sublabelTone: 'neutral',
        sparkData: [71, 73, 74, 75, 76, 77, 77.5, 78],
        footerInitial: 'M',
        footerName: 'Mark',
        footerSource: 'Hubspot',
        footerFrequency: 'Wekelijks',
    },
    {
        title: '# Tickets',
        value: '156',
        sublabel: '+12',
        sublabelTone: 'positive',
        sparkData: [118, 125, 132, 138, 142, 148, 152, 156],
        footerInitial: 'S',
        footerName: 'Sanne',
        footerSource: 'Zendesk',
        footerFrequency: 'Wekelijks',
    },
    {
        title: '# Occupancy Rate',
        value: '78%',
        sublabel: 'stabiel',
        sublabelTone: 'neutral',
        sparkData: [74, 75, 76, 76.5, 77, 77.5, 78, 78],
        footerInitial: 'T',
        footerName: 'Team Ops',
        footerSource: 'WMS',
        footerFrequency: 'Dagelijks',
    },
    {
        title: `Storage Lead Time (${props.teamCode})`,
        value: '2,3 dgn',
        sublabel: 'indicatief',
        sublabelTone: 'neutral',
        sparkData: [3.4, 3.1, 2.9, 2.8, 2.65, 2.5, 2.4, 2.3],
        sparkDotted: true,
        footerInitial: 'K',
        footerName: 'Karin',
        footerSource: 'Excel',
        footerFrequency: 'Wekelijks',
    },
]);

const hrCardPt = {
    root: { class: 'border border-gray-100 shadow-sm h-full' },
    body: { class: '!p-0' },
    content: { class: '!p-5 flex flex-col gap-2' },
};

const filterStartId = computed(() => `filter-start-${props.teamCode}`);
const filterEndId = computed(() => `filter-end-${props.teamCode}`);
const filterCoId = computed(() => `filter-co-${props.teamCode}`);
</script>

<template>
    <Head :title="pageTitle" />

    <ManagementLayout>
        <div class="mx-auto max-w-[1600px] px-4 py-6 lg:px-6">
            <div
                class="mb-6 rounded-2xl bg-black px-6 py-8 text-white shadow-lg sm:px-10 sm:py-10"
            >
                <h1 class="text-2xl font-bold tracking-tight sm:text-3xl">
                    Dashboard Rapportage
                </h1>
                <div
                    class="mt-4 flex flex-wrap gap-x-8 gap-y-2 text-sm text-white/90"
                >
                    <span>
                        Team:
                        <strong class="text-white">{{ teamCode }}</strong>
                    </span>
                    <span>
                        Datum:
                        <strong class="text-white">{{ heroDatum }}</strong>
                    </span>
                </div>
            </div>

            <div
                class="mb-6 grid grid-cols-1 gap-5 rounded-xl border border-gray-100 bg-white p-5 shadow-sm md:grid-cols-3"
            >
                <div>
                    <label :class="filterLabel" :for="filterStartId">
                        Startdatum
                    </label>
                    <DatePicker
                        :id="filterStartId"
                        v-model="startDate"
                        date-format="dd-mm-yy"
                        show-icon
                        fluid
                        icon-display="input"
                    />
                </div>
                <div>
                    <label :class="filterLabel" :for="filterEndId">
                        Einddatum
                    </label>
                    <DatePicker
                        :id="filterEndId"
                        v-model="endDate"
                        date-format="dd-mm-yy"
                        show-icon
                        fluid
                        icon-display="input"
                    />
                </div>
                <div class="md:col-span-1">
                    <label :class="filterLabel" :for="filterCoId">
                        Filter op bedrijf
                    </label>
                    <MultiSelect
                        :id="filterCoId"
                        v-model="companies"
                        :options="companyOptions"
                        placeholder="Selecteer bedrijven"
                        display="comma"
                        fluid
                        :max-selected-labels="2"
                    />
                </div>
            </div>

            <div
                class="mb-6 rounded-xl border border-red-200 bg-red-50/90 px-5 py-4"
            >
                <p
                    class="text-[11px] font-semibold uppercase tracking-wide text-[#ff7020]"
                >
                    Waarschuwingsregel
                </p>
                <p class="mt-1 text-sm font-medium text-gray-900">
                    Tickets open &gt; 24 uur zonder reactie
                </p>
            </div>

            <section class="mb-10">
                <h2 :class="[sectionOrange, 'mb-4 leading-snug']">
                    Belangrijkste gedeelde strategische, operationele en tactische
                    KPI's
                </h2>
                <div
                    class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5"
                >
                    <RapportageKpiCard
                        v-for="(k, i) in sharedKpis"
                        :key="`${teamCode}-kpi-${i}`"
                        :title="k.title"
                        :value="k.value"
                        :placeholder="!!k.placeholder"
                        :sublabel="k.sublabel"
                        :sublabel-tone="k.sublabelTone ?? 'neutral'"
                        :spark-data="k.sparkData"
                        :spark-dotted="!!k.sparkDotted"
                        :footer-initial="k.footerInitial"
                        :footer-name="k.footerName"
                        :footer-source="k.footerSource"
                        :footer-frequency="k.footerFrequency"
                    />
                </div>
            </section>

            <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
                <section>
                    <h2 :class="[sectionOrange, 'mb-4']">HR</h2>
                    <Card :pt="hrCardPt">
                        <template #content>
                            <div class="flex items-start justify-between gap-2">
                                <h3
                                    class="text-sm font-semibold text-gray-900"
                                >
                                    eNPS
                                </h3>
                                <button
                                    type="button"
                                    class="text-gray-400 hover:text-gray-600"
                                    aria-label="Info"
                                >
                                    <i class="pi pi-info-circle text-sm" />
                                </button>
                            </div>
                            <p class="mt-2 text-3xl font-bold text-gray-900">
                                +42
                            </p>
                            <p class="mt-3 border-t border-gray-100 pt-3 text-xs text-gray-500">
                                HR · Kwartaal
                            </p>
                        </template>
                    </Card>
                </section>
                <section>
                    <h2 :class="[sectionOrange, 'mb-4']">
                        Klanttevredenheid
                    </h2>
                    <Card :pt="hrCardPt">
                        <template #content>
                            <div class="flex items-start justify-between gap-2">
                                <h3
                                    class="text-sm font-semibold text-gray-900"
                                >
                                    NPS
                                </h3>
                                <button
                                    type="button"
                                    class="text-gray-400 hover:text-gray-600"
                                    aria-label="Info"
                                >
                                    <i class="pi pi-info-circle text-sm" />
                                </button>
                            </div>
                            <p class="mt-2 text-3xl font-bold text-gray-900">
                                +56
                            </p>
                            <p class="mt-3 border-t border-gray-100 pt-3 text-xs text-gray-500">
                                CX · Maandelijks
                            </p>
                        </template>
                    </Card>
                </section>
            </div>
        </div>
    </ManagementLayout>
</template>
