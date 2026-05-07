<script setup>
import ManagementLayout from '@/Layouts/ManagementLayout.vue';
import { Head } from '@inertiajs/vue3';
import { ref } from 'vue';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Chart from 'primevue/chart';
import SelectButton from 'primevue/selectbutton';
import Tag from 'primevue/tag';

const period = ref('Maand');
const periods = ref(['Week', 'Maand', 'Kwartaal']);

const brandBlue = '#1e3a5f';

const lineChartData = ref({
    labels: [
        'Apr',
        'Mei',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Okt',
        'Nov',
        'Dec',
        'Jan',
        'Feb',
        'Mrt',
    ],
    datasets: [
        {
            label: 'Omzet',
            data: [
                380, 392, 410, 425, 438, 455, 448, 462, 478, 490, 502, 518,
            ],
            borderColor: brandBlue,
            backgroundColor: brandBlue,
            pointBackgroundColor: brandBlue,
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            tension: 0.35,
            fill: false,
        },
    ],
});

const lineChartOptions = ref({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false,
        },
    },
    scales: {
        x: {
            grid: {
                color: '#e5e5e5',
                borderDash: [4, 4],
            },
            ticks: {
                color: '#6b7280',
            },
        },
        y: {
            min: 0,
            max: 600,
            grid: {
                color: '#e5e5e5',
                borderDash: [4, 4],
            },
            ticks: {
                color: '#6b7280',
            },
        },
    },
});

const barChartData = ref({
    labels: ['STELZ', 'LogParts', 'TechFlow', 'BrightGoods', 'NordShip'],
    datasets: [
        {
            label: 'Volume',
            data: [3050, 2760, 2420, 1980, 1650],
            backgroundColor: brandBlue,
            borderRadius: 4,
            barThickness: 24,
        },
    ],
});

const barChartOptions = ref({
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false,
        },
    },
    scales: {
        x: {
            min: 0,
            max: 3200,
            grid: {
                color: '#e5e5e5',
                borderDash: [4, 4],
            },
            ticks: {
                color: '#6b7280',
            },
        },
        y: {
            grid: {
                display: false,
            },
            ticks: {
                color: '#374151',
            },
        },
    },
});

const kpiCardPt = {
    root: { class: 'border border-gray-100 shadow-sm' },
    body: { class: '!p-0' },
    caption: { class: '!px-6 !pt-6 !pb-4' },
    title: { class: '!mb-0 !text-sm !font-medium !text-gray-600' },
    content: { class: '!px-6 !pb-6 !pt-0' },
};

const chartCardPt = {
    root: { class: 'border border-gray-100 shadow-sm' },
    body: { class: '!p-0' },
    caption: { class: '!px-6 !pt-6 !pb-5' },
    title: { class: '!mb-0 !text-base !font-semibold !text-gray-900' },
    content: { class: '!px-6 !pb-6 !pt-0' },
};
</script>

<template>
    <Head title="Management Dashboard" />

    <ManagementLayout>
        <div class="mx-auto max-w-[1600px] px-4 py-6 lg:px-6">
            <div
                class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
            >
                <h1 class="text-2xl font-semibold tracking-tight text-gray-900">
                    Management Dashboard
                </h1>
                <SelectButton
                    v-model="period"
                    :options="periods"
                    :allow-empty="false"
                />
            </div>

            <div
                class="mb-6 flex flex-col gap-4 rounded-lg border border-orange-100 bg-[#fff3eb] p-4 sm:flex-row sm:items-center"
            >
                <div
                    class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#ff7020]/15 text-[#ff7020]"
                >
                    <i class="pi pi-bell text-xl" />
                </div>
                <div class="min-w-0 flex-1">
                    <p class="font-medium text-gray-900">
                        Het dagrapport van 15:00 is beschikbaar
                    </p>
                    <p class="text-sm text-gray-600">
                        3 nieuwe reacties van teamleiders
                    </p>
                </div>
                <Button label="Bekijk rapport" class="shrink-0 self-start sm:self-auto" />
            </div>

            <div
                class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
            >
                <Card :pt="kpiCardPt">
                    <template #title> Service Level </template>
                    <template #content>
                        <p class="mb-1 text-3xl font-bold text-gray-900">
                            97,2%
                        </p>
                        <p class="mb-3 text-xs text-gray-500">
                            Doel: ≥ 95%
                        </p>
                        <Tag value="Op target" severity="success" />
                    </template>
                </Card>

                <Card :pt="kpiCardPt">
                    <template #title> Palletbezetting </template>
                    <template #content>
                        <p class="mb-1 text-3xl font-bold text-gray-900">81%</p>
                        <p class="mb-3 text-xs text-gray-500">
                            Doel: ≥ 75%
                        </p>
                        <Tag value="Op target" severity="success" />
                    </template>
                </Card>

                <Card :pt="kpiCardPt">
                    <template #title> Foutenpercentage </template>
                    <template #content>
                        <p class="mb-1 text-3xl font-bold text-gray-900">
                            0,4%
                        </p>
                        <p class="mb-3 text-xs text-gray-500">
                            Doel: ≤ 0,5%
                        </p>
                        <div class="flex flex-wrap gap-2">
                            <Tag value="4 open" severity="danger" />
                            <Tag value="Op target" severity="success" />
                        </div>
                    </template>
                </Card>

                <Card :pt="kpiCardPt">
                    <template #title> Omzet maart </template>
                    <template #content>
                        <p class="mb-1 text-3xl font-bold text-gray-900">
                            €520K
                        </p>
                        <p class="mb-3 text-xs text-gray-500">
                            Doel: €500K
                        </p>
                        <Tag value="Op target" severity="success" />
                    </template>
                </Card>
            </div>

            <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <Card :pt="chartCardPt">
                    <template #title> Omzet trend (12 maanden) </template>
                    <template #content>
                        <div class="h-[280px] w-full">
                            <Chart
                                type="line"
                                :data="lineChartData"
                                :options="lineChartOptions"
                                class="h-full w-full"
                            />
                        </div>
                    </template>
                </Card>

                <Card :pt="chartCardPt">
                    <template #title> Top 5 klanten (volume) </template>
                    <template #content>
                        <div class="h-[280px] w-full">
                            <Chart
                                type="bar"
                                :data="barChartData"
                                :options="barChartOptions"
                                class="h-full w-full"
                            />
                        </div>
                    </template>
                </Card>
            </div>

            <div
                class="mt-8 flex flex-col gap-2 border-t border-gray-200 pt-4 text-sm text-gray-500 sm:flex-row sm:items-center sm:justify-between"
            >
                <span>
                    Rapportage door Amsterdam Warehouse Company |
                    Maandelijks
                </span>
                <span class="font-medium text-[#ff7020]">
                    The place to go
                </span>
            </div>
        </div>
    </ManagementLayout>
</template>
