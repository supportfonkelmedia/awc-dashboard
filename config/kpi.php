<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Fixture data (Acceptatietest 22 sep 2026: local UI zonder Peliqan)
    |--------------------------------------------------------------------------
    |
    | KPI_USE_FIXTURE=true  → altijd fixtures.
    | KPI_FALLBACK_FIXTURE  → in local: fixtures als PELIQAN_KPI_DATA_URL ontbreekt.
    |
    */
    'use_fixture' => filter_var(env('KPI_USE_FIXTURE', false), FILTER_VALIDATE_BOOL),

    'fallback_fixture' => filter_var(
        env('KPI_FALLBACK_FIXTURE', env('APP_ENV') === 'local'),
        FILTER_VALIDATE_BOOL,
    ),

];
