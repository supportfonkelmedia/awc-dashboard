<script setup>
import SidebarNav from '@/Components/Management/SidebarNav.vue';
import Button from 'primevue/button';
import Drawer from 'primevue/drawer';
import { Link } from '@inertiajs/vue3';
import { ref } from 'vue';

const mobileNavOpen = ref(false);

function closeMobileNav() {
    mobileNavOpen.value = false;
}
</script>

<template>
    <div class="flex min-h-screen bg-[#f4f4f4] font-sans antialiased">
        <aside
            class="hidden w-64 shrink-0 flex-col bg-[#1a1a1a] text-gray-200 lg:flex"
        >
            <div class="flex flex-1 flex-col overflow-y-auto pt-6">
                <SidebarNav />
            </div>
        </aside>

        <div class="flex min-h-screen min-w-0 flex-1 flex-col">
            <header
                class="flex h-[3.25rem] shrink-0 items-center justify-between bg-[#252525] px-4 text-white lg:px-6"
            >
                <div class="flex min-w-0 flex-1 items-center gap-3">
                    <Button
                        icon="pi pi-bars"
                        severity="secondary"
                        text
                        rounded
                        aria-label="Menu"
                        class="shrink-0 !text-white lg:!hidden"
                        @click="mobileNavOpen = true"
                    />
                    <div class="flex min-w-0 flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-3">
                        <div class="flex min-w-0 items-center gap-3">
                            <div
                                class="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-[#ff7020]/20 text-[#ff7020]"
                            >
                                <i class="pi pi-box text-lg" />
                            </div>
                            <span
                                class="truncate text-[11px] font-semibold uppercase tracking-wide text-white sm:text-xs"
                            >
                                Amsterdam Warehouse Co.
                            </span>
                        </div>
                        <span
                            class="hidden truncate text-sm font-medium text-white/85 sm:inline sm:text-base"
                        >
                            Data &amp; Application Platform
                        </span>
                    </div>
                </div>

                <div
                    class="flex shrink-0 items-center gap-2 md:gap-4 lg:gap-6"
                >
                    <span class="hidden max-w-[140px] truncate text-sm text-white/90 lg:inline">
                        {{ $page.props.auth.user.name }}
                    </span>
                    <span
                        class="hidden rounded-full bg-black/40 px-3 py-1 text-xs font-medium text-white/90 ring-1 ring-white/10 xl:inline"
                    >
                        Management / MT
                    </span>
                    <span
                        class="rounded-full bg-[#ff7020] px-3 py-1 text-xs font-semibold text-white shadow-sm"
                    >
                        Management
                    </span>
                    <Link
                        :href="route('logout')"
                        method="post"
                        as="button"
                        class="flex items-center gap-2 border-none bg-transparent text-sm text-white/75 transition hover:text-white"
                    >
                        <i class="pi pi-sign-out" />
                        <span class="hidden md:inline">Uitloggen</span>
                    </Link>
                </div>
            </header>

            <main class="flex-1 overflow-auto">
                <slot />
            </main>
        </div>

        <Drawer
            v-model:visible="mobileNavOpen"
            position="left"
            class="management-drawer !w-[min(18rem,85vw)] border-none bg-[#1a1a1a]"
            :pt="{
                root: { class: '!shadow-2xl' },
                header: { class: '!hidden' },
                content: { class: '!p-0 overflow-y-auto' },
            }"
        >
            <SidebarNav :on-navigate="closeMobileNav" />
        </Drawer>
    </div>
</template>

<style scoped>
.management-drawer :deep(.p-drawer-content) {
    background-color: #1a1a1a;
}
</style>
