<script setup>
/**
 * KPI dashboard only: no Fonkel Management chrome (sidebar / top bar).
 * For embedding in another platform; auth and parent UI live outside this shell.
 */
</script>

<template>
    <div class="min-h-screen bg-awc-platinum font-sans antialiased">
        <slot />
    </div>
</template>
