<?php

return [

    /*
    |--------------------------------------------------------------------------
    | API JWT
    |--------------------------------------------------------------------------
    |
    | Token from Peliqan: Settings / Security → API token.
    | Send as: Authorization: JWT {token}
    |
    */
    'token' => env('PELIQAN_JWT', ''),

    /*
    |--------------------------------------------------------------------------
    | Request timeout (seconds)
    |--------------------------------------------------------------------------
    */
    'timeout' => (int) env('PELIQAN_TIMEOUT', 60),

    /*
    |--------------------------------------------------------------------------
    | Published endpoint URL (no query string)
    |--------------------------------------------------------------------------
    |
    | "Final URL" of the KPI API endpoint in Peliqan (peliqan_kpi_api_handler.py).
    | Example: https://api.eu.peliqan.io/2401/kpi/data
    |
    */
    'kpi_data_url' => env('PELIQAN_KPI_DATA_URL', ''),

    /*
    | KPI cache TTL (seconds); 0 = no cache. Overdracht: max ~1 uur.
    */
    'kpi_cache_ttl' => (int) env('PELIQAN_KPI_CACHE_TTL', 3600),

    /*
    | Drills op live Sprinter-views (AFC-analyse): de handler haalt Sprinter zelf hooguit 1x per minuut op,
    | dus hier geen uur-cache. 0 = altijd vers (het laatste goede antwoord blijft de terugval bij storing).
    */
    'kpi_live_cache_ttl' => (int) env('PELIQAN_KPI_LIVE_CACHE_TTL', 0),

    /*
    | Views die op live Sprinter-data rusten (handler v11, SPRINTER_LIVE_VIEWS).
    */
    'kpi_live_views' => [
        'kpi_afc_zending_maand',
        'kpi_afc_eigenaar_maand',
        'kpi_afc_klant_jaar',
        'kpi_afc_klant',
        'kpi_afc_klant_retentie_jaar',
    ],

    /*
    | Log full GET query + response body to storage/logs/peliqan-*.log (see logging.channels.peliqan).
    */
    'http_log' => filter_var(env('PELIQAN_HTTP_LOG', false), FILTER_VALIDATE_BOOL),

    'http_log_max_body' => (int) env('PELIQAN_HTTP_LOG_MAX_BODY', 100_000),

    'http_log_cache_hits' => filter_var(
        env('PELIQAN_HTTP_LOG_CACHE_HITS', true),
        FILTER_VALIDATE_BOOL,
    ),

];
