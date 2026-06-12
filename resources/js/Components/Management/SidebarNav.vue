<script setup>
import { Link } from '@inertiajs/vue3';

defineProps({
    onNavigate: {
        type: Function,
        default: null,
    },
});

const rowPad = 'px-4 py-2.5';
const sectionTitlePad = 'px-4 pb-2 pt-0';
const iconWrap =
    'flex size-6 shrink-0 items-center justify-center text-[0.9375rem] leading-none';

const operActiveBar =
    'bg-white/[0.06] font-medium text-white before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:bg-[#ff7020]';
const operInactive = 'text-gray-300 hover:bg-white/5 hover:text-white';
const operRow = `${rowPad} relative flex w-full items-center gap-3 text-sm transition`;

function operClasses(routeName) {
    return [operRow, route().current(routeName) ? operActiveBar : operInactive];
}

function operIconClass(routeName) {
    return route().current(routeName) ? 'text-[#ff7020]' : 'text-gray-400';
}
</script>

<template>
    <div class="flex flex-col gap-8 pb-6">
        <div>
            <p
                :class="[
                    sectionTitlePad,
                    'text-xs font-semibold uppercase tracking-wider text-gray-500',
                ]"
            >
                Management
            </p>
            <p
                :class="[
                    sectionTitlePad,
                    '-mt-1 text-xs font-semibold uppercase tracking-wider text-[#ff7020]',
                ]"
            >
                MT
            </p>
            <nav class="flex flex-col gap-px">
                <Link
                    :href="route('mt.dashboard')"
                    :class="[
                        rowPad,
                        'relative flex w-full items-center gap-3 text-sm transition',
                        route().current('mt.dashboard')
                            ? 'bg-white/[0.06] font-medium text-white before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:bg-[#ff7020]'
                            : 'text-gray-300 hover:bg-white/5 hover:text-white',
                    ]"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-chart-bar"
                            :class="
                                route().current('mt.dashboard')
                                    ? 'text-[#ff7020]'
                                    : 'text-gray-400'
                            "
                        />
                    </span>
                    MT Dashboard
                </Link>
                <Link
                    :href="route('awc.dashboard')"
                    :class="[
                        rowPad,
                        'relative flex w-full items-center gap-3 rounded-md text-sm transition',
                        route().current('awc.dashboard')
                            ? 'bg-white/[0.08] font-medium text-white shadow-[0_0_14px_rgba(56,189,248,0.28)] ring-1 ring-sky-400/65 before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:rounded-l-md before:bg-sky-400'
                            : 'text-gray-300 hover:bg-white/5 hover:text-white',
                    ]"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-warehouse"
                            :class="
                                route().current('awc.dashboard')
                                    ? 'text-sky-300'
                                    : 'text-gray-400'
                            "
                        />
                    </span>
                    AWC
                </Link>
                <Link
                    :href="route('afc.dashboard')"
                    :class="[
                        rowPad,
                        'relative flex w-full items-center gap-3 rounded-md text-sm transition',
                        route().current('afc.dashboard')
                            ? 'bg-white/[0.08] font-medium text-white shadow-[0_0_14px_rgba(56,189,248,0.28)] ring-1 ring-sky-400/65 before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:rounded-l-md before:bg-sky-400'
                            : 'text-gray-300 hover:bg-white/5 hover:text-white',
                    ]"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-truck"
                            :class="
                                route().current('afc.dashboard')
                                    ? 'text-sky-300'
                                    : 'text-gray-400'
                            "
                        />
                    </span>
                    AFC
                </Link>
                <Link
                    :href="route('acc.dashboard')"
                    :class="[
                        rowPad,
                        'relative flex w-full items-center gap-3 rounded-md text-sm transition',
                        route().current('acc.dashboard')
                            ? 'bg-white/[0.08] font-medium text-white shadow-[0_0_14px_rgba(56,189,248,0.28)] ring-1 ring-sky-400/65 before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:rounded-l-md before:bg-sky-400'
                            : 'text-gray-300 hover:bg-white/5 hover:text-white',
                    ]"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-building"
                            :class="
                                route().current('acc.dashboard')
                                    ? 'text-sky-300'
                                    : 'text-gray-400'
                            "
                        />
                    </span>
                    ACC
                </Link>
            </nav>
        </div>

        <div>
            <p
                :class="[
                    sectionTitlePad,
                    'text-xs font-semibold uppercase tracking-wider text-[#ff7020]',
                ]"
            >
                Operationeel
            </p>
            <nav class="flex flex-col gap-px">
                <Link
                    :href="route('dashboard')"
                    :class="[
                        rowPad,
                        'relative flex w-full items-center gap-3 text-sm transition',
                        route().current('dashboard')
                            ? 'bg-white/[0.06] font-medium text-white before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:bg-[#ff7020]'
                            : 'text-gray-300 hover:bg-white/5 hover:text-white',
                    ]"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-th-large"
                            :class="
                                route().current('dashboard')
                                    ? 'text-[#ff7020]'
                                    : 'text-gray-400'
                            "
                        />
                    </span>
                    Dashboard
                </Link>
                <Link
                    :href="route('operationeel.errors')"
                    :class="operClasses('operationeel.errors')"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-exclamation-triangle"
                            :class="operIconClass('operationeel.errors')"
                        />
                    </span>
                    Foutenoverzicht
                </Link>
                <Link
                    :href="route('operationeel.reports')"
                    :class="operClasses('operationeel.reports')"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-file"
                            :class="operIconClass('operationeel.reports')"
                        />
                    </span>
                    Rapportages
                </Link>
                <Link
                    :href="route('operationeel.communication')"
                    :class="operClasses('operationeel.communication')"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-comments"
                            :class="operIconClass('operationeel.communication')"
                        />
                    </span>
                    Communicatie
                </Link>
                <Link
                    :href="route('operationeel.teams')"
                    :class="operClasses('operationeel.teams')"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-users"
                            :class="operIconClass('operationeel.teams')"
                        />
                    </span>
                    Mijn Teams
                </Link>
                <Link
                    :href="route('operationeel.tools')"
                    :class="operClasses('operationeel.tools')"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-wrench"
                            :class="operIconClass('operationeel.tools')"
                        />
                    </span>
                    Tools
                </Link>
                <Link
                    v-if="$page.props.appDebug"
                    :href="route('debug.peliqan.7t')"
                    :class="operClasses('debug.peliqan.7t')"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-database"
                            :class="operIconClass('debug.peliqan.7t')"
                        />
                    </span>
                    7T Debug
                </Link>
                <Link
                    :href="route('operationeel.users')"
                    :class="operClasses('operationeel.users')"
                    @click="onNavigate?.()"
                >
                    <span :class="iconWrap">
                        <i
                            class="pi pi-user"
                            :class="operIconClass('operationeel.users')"
                        />
                    </span>
                    Gebruikers
                </Link>
            </nav>
        </div>

        <div class="mt-auto border-t border-white/10 px-4 pt-6">
            <p class="text-[10px] uppercase tracking-widest text-gray-500">
                AWC Platform v1.0
            </p>
        </div>
    </div>
</template>
