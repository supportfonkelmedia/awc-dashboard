import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';

export default definePreset(Aura, {
    primitive: {
        // Pumpkin Orange uit de AWC-huisstijl, met donkerder tinten voor hover/active.
        orange: {
            500: '#FF6700',
            600: '#E05A00',
            700: '#B84A00',
        },
    },
    semantic: {
        primary: {
            50: '{orange.50}',
            100: '{orange.100}',
            200: '{orange.200}',
            300: '{orange.300}',
            400: '{orange.400}',
            500: '{orange.500}',
            600: '{orange.600}',
            700: '{orange.700}',
            800: '{orange.800}',
            900: '{orange.900}',
            950: '{orange.950}',
        },
    },
});
