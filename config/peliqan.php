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
    | Published endpoint URLs (no query string)
    |--------------------------------------------------------------------------
    |
    | Paste the "Final URL" from each API endpoint in Peliqan, without ?…
    | Example: https://api.eu.peliqan.io/2401/awc/data
    |
    */
    'awc_data_url' => env('PELIQAN_AWC_DATA_URL', ''),
    'mt_data_url' => env('PELIQAN_MT_DATA_URL', ''),

    /*
    |--------------------------------------------------------------------------
    | MT dashboard cache TTL (seconds); 0 = disable Cache::remember for Peliqan
    |--------------------------------------------------------------------------
    */
    'cache_ttl' => (int) env('PELIQAN_CACHE_TTL', 120),

];
