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
    | 7T WMS — slower Trino/SQL Server; separate timeout + longer cache
    |--------------------------------------------------------------------------
    */
    'wms_timeout' => (int) env('PELIQAN_WMS_TIMEOUT', 120),
    'wms_cache_ttl' => (int) env('PELIQAN_WMS_CACHE_TTL', 600),

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
    'schema_7t_url' => env('PELIQAN_7T_SCHEMA_URL', ''),

    /*
    | 7T WMS — own endpoint (direct SQL Server handler, no Trino).
    | Example: https://api.eu.peliqan.io/2401/awc/7t
    */
    'awc_7t_url' => env('PELIQAN_AWC_7T_URL', ''),

    /*
    |--------------------------------------------------------------------------
    | MT dashboard cache TTL (seconds); 0 = disable Cache::remember for Peliqan
    |--------------------------------------------------------------------------
    */
    'cache_ttl' => (int) env('PELIQAN_CACHE_TTL', 120),

];
