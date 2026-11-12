<script setup>
import { Link } from '@inertiajs/vue3';
import {
    KPI_PRIMARY_TABS,
    KPI_TEAM_TABS,
    isKpiTabActive,
    kpiScreenRoute,
} from '@/constants/kpiScreens';

defineProps({
    scherm: {
        type: String,
        required: true,
    },
});
</script>

<template>
    <div class="border-b border-gray-200 bg-white">
        <div
            class="mx-auto flex max-w-[1440px] flex-wrap items-stretch px-4 lg:px-8"
        >
            <!-- Same box as the tabs (h-12 + 2px transparent border) so text centers identically -->
            <span
                class="flex h-12 items-center border-b-2 border-transparent pr-4 text-sm leading-5 text-gray-400"
            >
                Concern
            </span>
            <nav
                class="flex flex-wrap items-stretch text-sm font-medium"
                aria-label="KPI-niveau"
            >
                <Link
                    v-for="tab in KPI_PRIMARY_TABS"
                    :key="tab.id"
                    :href="kpiScreenRoute(tab.scherm)"
                    :class="[
                        'flex h-12 items-center border-b-2 px-3 leading-5 transition',
                        isKpiTabActive(tab.scherm, scherm)
                            ? 'border-awc-orange text-awc-orange'
                            : 'border-transparent text-gray-600 hover:text-gray-900',
                    ]"
                >
                    {{ tab.label }}
                </Link>
            </nav>

            <span
                class="mx-8 hidden h-12 items-center border-b-2 border-transparent sm:flex"
                aria-hidden="true"
            >
                <span class="h-5 w-px bg-gray-300" />
            </span>

            <span
                class="flex h-12 items-center border-b-2 border-transparent pr-4 text-sm leading-5 text-gray-400"
            >
                Teams
            </span>

            <nav
                class="flex flex-wrap items-stretch text-sm font-medium"
                aria-label="KPI-teams"
            >
                <Link
                    v-for="tab in KPI_TEAM_TABS"
                    :key="tab.id"
                    :href="kpiScreenRoute(tab.scherm)"
                    :class="[
                        'flex h-12 items-center border-b-2 px-3 leading-5 transition',
                        isKpiTabActive(tab.scherm, scherm)
                            ? 'border-awc-orange text-awc-orange'
                            : 'border-transparent text-gray-600 hover:text-gray-900',
                    ]"
                >
                    {{ tab.label }}
                </Link>
            </nav>
        </div>
    </div>
</template>
