import defaultTheme from 'tailwindcss/defaultTheme';
import colors from 'tailwindcss/colors';
import forms from '@tailwindcss/forms';

/**
 * AWC-huisstijl (Figma "AWC Huisttijl", Stijlgids AWC):
 * primair Black, Platinum Light en Pure White; accenten Pumpkin Orange en
 * Celestial Blue. Lettertype Volksans; Manrope is de placeholder tot er een
 * webversie van Volksans is. Grijs is neutraal (geen blauwzweem), passend bij
 * zwart en platinum.
 *
 * @type {import('tailwindcss').Config}
 */
export default {
    content: [
        './vendor/laravel/framework/src/Illuminate/Pagination/resources/views/*.blade.php',
        './storage/framework/views/*.php',
        './resources/views/**/*.blade.php',
        './resources/js/**/*.vue',
    ],

    theme: {
        extend: {
            fontFamily: {
                sans: ['Manrope', ...defaultTheme.fontFamily.sans],
            },
            colors: {
                gray: colors.neutral,
                awc: {
                    black: '#000000',
                    platinum: '#EBEBEB',
                    white: '#FFFFFF',
                    orange: '#FF6700',
                    'orange-dark': '#E05A00',
                    blue: '#0496FF',
                },
            },
        },
    },

    plugins: [forms],
};
