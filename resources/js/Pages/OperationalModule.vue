<script setup>
import ManagementLayout from '@/Layouts/ManagementLayout.vue';
import { Head } from '@inertiajs/vue3';
import { computed } from 'vue';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Tag from 'primevue/tag';

const props = defineProps({
    module: {
        type: String,
        required: true,
        validator: (v) =>
            ['errors', 'reports', 'communication', 'teams', 'tools', 'users'].includes(
                v,
            ),
    },
});

const META = {
    errors: {
        pageTitle: 'Foutenoverzicht',
        heading: 'Foutenoverzicht',
        lead: 'Open meldingen en incidenten uit WMS, ticketing en integraties.',
    },
    reports: {
        pageTitle: 'Rapportages',
        heading: 'Rapportages',
        lead: 'Geplande en handmatige rapportages voor teams en het MT.',
    },
    communication: {
        pageTitle: 'Communicatie',
        heading: 'Communicatie',
        lead: 'Kanalen en afspraken voor interne en klantcommunicatie.',
    },
    teams: {
        pageTitle: 'Mijn teams',
        heading: 'Mijn teams',
        lead: 'Overzicht van teams waarvan u lid bent of die u volgt.',
    },
    tools: {
        pageTitle: 'Tools',
        heading: 'Tools',
        lead: 'Snelkoppelingen naar ondersteunende applicaties en utilities.',
    },
    users: {
        pageTitle: 'Gebruikers',
        heading: 'Gebruikers',
        lead: 'Platformaccounts en rollen (demo-data; koppel later aan directory).',
    },
};

const meta = computed(() => META[props.module]);

const cardShell = {
    root: { class: 'border border-gray-100 shadow-sm' },
    body: { class: '!p-0' },
    content: { class: '!p-0' },
};

const errorRows = [
    {
        code: 'INT-042',
        description: 'Webhook HubSpot → WMS time-out',
        severity: 'Hoog',
        since: '26 uur',
        status: 'Open',
    },
    {
        code: 'EDI-109',
        description: 'Berichtpartij geweigerd door mapping ACC',
        severity: 'Medium',
        since: '6 uur',
        status: 'In behandeling',
    },
    {
        code: 'WH-008',
        description: 'Scanner offline zone B — AFC',
        severity: 'Laag',
        since: '2 uur',
        status: 'Open',
    },
];

const reportRows = [
    {
        naam: 'Dagelijkse omzet AWC',
        type: 'Automatisch',
        periode: 'Dagelijks 06:00',
        laatste_run: '30-04-2026 06:03',
    },
    {
        naam: 'SLA tickets MT',
        type: 'Automatisch',
        periode: 'Wekelijks ma',
        laatste_run: '28-04-2026 07:15',
    },
    {
        naam: 'Voorraad AFC vs actuals',
        type: 'Handmatig',
        periode: 'Op aanvraag',
        laatste_run: '22-04-2026 14:40',
    },
];

const channels = [
    {
        title: 'Slack · #ops-alerts',
        body: 'Realtime meldingen voor warehouse en IT — alle piketleden.',
        icon: 'pi-comments',
    },
    {
        title: 'E-mail · servicedesk@awc.nl',
        body: 'Officieel kanaal voor klanttickets en escalaties naar Support.',
        icon: 'pi-envelope',
    },
    {
        title: 'Teams · MT updates',
        body: 'Wekelijkse samenvatting en besluitvragen voor het MT.',
        icon: 'pi-video',
    },
];

const teamCards = [
    { naam: 'Warehouse AWC', leden: 24, rol: 'Lead picking' },
    { naam: 'Transport AFC', leden: 12, rol: 'Planner' },
    { naam: 'Finance ACC', leden: 8, rol: 'Viewer' },
];

const toolCards = [
    { naam: 'WMS console', hint: 'Order- en voorraadstatus', icon: 'pi-box' },
    { naam: 'Ticketportal', hint: 'Zendesk agentweergave', icon: 'pi-ticket' },
    { naam: 'Integratiemonitor', hint: 'API health & retries', icon: 'pi-chart-line' },
    { naam: 'Doc hub', hint: 'Handleidingen & runbooks', icon: 'pi-book' },
];

const userRows = [
    {
        naam: 'Mark Zomerdijk',
        email: 'mark.zomerdijk@example.com',
        rol: 'Management',
    },
    {
        naam: 'Sanne de Vries',
        email: 'sanne.devries@example.com',
        rol: 'Operationeel',
    },
    {
        naam: 'Tom Bakker',
        email: 'tom.bakker@example.com',
        rol: 'Administrator',
    },
];

function severityTag(sev) {
    const s = String(sev).toLowerCase();
    if (s.includes('hoog')) return 'danger';
    if (s.includes('medium')) return 'warn';
    return 'secondary';
}

function statusTag(st) {
    const s = String(st).toLowerCase();
    if (s.includes('open')) return 'danger';
    if (s.includes('behandeling')) return 'warn';
    return 'success';
}

function rolTag(rol) {
    const r = String(rol).toLowerCase();
    if (r.includes('admin')) return 'danger';
    if (r.includes('management')) return 'warn';
    return 'info';
}
</script>

<template>
    <Head :title="meta.pageTitle" />

    <ManagementLayout>
        <div class="mx-auto max-w-[1600px] px-4 py-6 lg:px-6">
            <header class="mb-8">
                <h1 class="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">
                    {{ meta.heading }}
                </h1>
                <p class="mt-2 max-w-3xl text-sm leading-relaxed text-gray-600">
                    {{ meta.lead }}
                </p>
            </header>

            <!-- Foutenoverzicht -->
            <Card v-if="module === 'errors'" :pt="cardShell">
                <template #content>
                    <DataTable
                        :value="errorRows"
                        striped-rows
                        class="text-sm"
                        :pt="{
                            root: { class: 'rounded-lg overflow-hidden' },
                        }"
                    >
                        <Column field="code" header="Code" class="font-mono text-xs" />
                        <Column field="description" header="Omschrijving" />
                        <Column field="severity" header="Ernst">
                            <template #body="{ data }">
                                <Tag :value="data.severity" :severity="severityTag(data.severity)" />
                            </template>
                        </Column>
                        <Column field="since" header="Sinds" />
                        <Column field="status" header="Status">
                            <template #body="{ data }">
                                <Tag :value="data.status" :severity="statusTag(data.status)" />
                            </template>
                        </Column>
                    </DataTable>
                </template>
            </Card>

            <!-- Rapportages -->
            <Card v-else-if="module === 'reports'" :pt="cardShell">
                <template #content>
                    <DataTable :value="reportRows" striped-rows class="text-sm">
                        <Column field="naam" header="Rapport" />
                        <Column field="type" header="Type" />
                        <Column field="periode" header="Periode / schema" />
                        <Column field="laatste_run" header="Laatste run" />
                    </DataTable>
                </template>
            </Card>

            <!-- Communicatie -->
            <div
                v-else-if="module === 'communication'"
                class="grid grid-cols-1 gap-4 md:grid-cols-3"
            >
                <Card
                    v-for="(c, i) in channels"
                    :key="i"
                    :pt="{
                        root: { class: 'border border-gray-100 shadow-sm h-full' },
                        body: { class: '!p-0' },
                        content: { class: '!p-5' },
                    }"
                >
                    <template #content>
                        <div class="flex gap-3">
                            <div
                                class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-[#ff7020]/12 text-[#ff7020]"
                            >
                                <i :class="['pi text-lg', c.icon]" />
                            </div>
                            <div class="min-w-0">
                                <h2 class="text-sm font-semibold text-gray-900">
                                    {{ c.title }}
                                </h2>
                                <p class="mt-2 text-xs leading-relaxed text-gray-600">
                                    {{ c.body }}
                                </p>
                            </div>
                        </div>
                    </template>
                </Card>
            </div>

            <!-- Mijn teams -->
            <div
                v-else-if="module === 'teams'"
                class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
            >
                <Card
                    v-for="(t, i) in teamCards"
                    :key="i"
                    :pt="{
                        root: { class: 'border border-gray-100 shadow-sm' },
                        body: { class: '!p-0' },
                        content: { class: '!p-5' },
                    }"
                >
                    <template #content>
                        <div class="flex items-start justify-between gap-3">
                            <div class="min-w-0">
                                <h2 class="text-base font-semibold text-gray-900">
                                    {{ t.naam }}
                                </h2>
                                <p class="mt-1 text-xs text-gray-500">
                                    Jouw rol: {{ t.rol }}
                                </p>
                            </div>
                            <Tag :value="`${t.leden} leden`" severity="secondary" />
                        </div>
                        <Button
                            label="Team openen"
                            text
                            size="small"
                            class="mt-4 !px-0 !text-[#ff7020]"
                            icon="pi pi-arrow-right"
                            icon-pos="right"
                        />
                    </template>
                </Card>
            </div>

            <!-- Tools -->
            <div
                v-else-if="module === 'tools'"
                class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
            >
                <Card
                    v-for="(tool, i) in toolCards"
                    :key="i"
                    :pt="{
                        root: {
                            class: 'border border-gray-100 shadow-sm transition hover:border-gray-200 hover:shadow-md cursor-pointer',
                        },
                        body: { class: '!p-0' },
                        content: { class: '!p-5' },
                    }"
                >
                    <template #content>
                        <div class="flex items-start gap-3">
                            <span
                                class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-gray-700"
                            >
                                <i :class="['pi text-lg', tool.icon]" />
                            </span>
                            <div class="min-w-0 flex-1">
                                <h2 class="text-sm font-semibold text-gray-900">
                                    {{ tool.naam }}
                                </h2>
                                <p class="mt-1 text-xs text-gray-500">
                                    {{ tool.hint }}
                                </p>
                            </div>
                            <i class="pi pi-external-link text-xs text-gray-400" />
                        </div>
                    </template>
                </Card>
            </div>

            <!-- Gebruikers -->
            <Card v-else-if="module === 'users'" :pt="cardShell">
                <template #content>
                    <DataTable :value="userRows" striped-rows class="text-sm">
                        <Column field="naam" header="Naam" />
                        <Column field="email" header="E-mail" />
                        <Column field="rol" header="Rol">
                            <template #body="{ data }">
                                <Tag :value="data.rol" :severity="rolTag(data.rol)" />
                            </template>
                        </Column>
                    </DataTable>
                </template>
            </Card>
        </div>
    </ManagementLayout>
</template>
