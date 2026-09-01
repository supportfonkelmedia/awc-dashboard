<?php

/**
 * MT KPI configuration — Brief Fonkel deel 1.
 * Defaults mirror peliqan_mt_api_handler.py (deploy both when changing wage accounts).
 */
return [

    'entities' => [
        'alaw' => [
            'code' => 'alaw',
            'label' => 'AWC',
            'close_lag_months' => 1,
        ],
        'pgl1' => [
            'code' => 'pgl1',
            'label' => 'AFC',
            'close_lag_months' => 2,
        ],
        'acco' => [
            'code' => 'acco',
            'label' => 'ACC',
            'close_lag_months' => 1,
        ],
    ],

    'excluded_admin_codes' => ['demo'],

    /**
     * Loonrekeningen per entiteit (financiële afdeling).
     * Pas aan wanneer besluit over ingehuurde arbeid valt — geen code-deploy nodig
     * als Peliqan-handler wage_accounts query-param accepteert.
     */
    'wage_accounts' => [
        'alaw' => ['4000', '4001', '4010', '40100', '40101', '4110', '4130', '4514'],
        'pgl1' => ['4010', '4011', '4110', '41100', '4130', '4512', '4514'],
        'acco' => ['4010', '4011', '4110', '41100', '4130', '4512', '4514'],
    ],

    /** Gedeeltelijk loon — apart tonen voor AFC/ACC (4130 pensioen, 4512 reis). */
    'partial_wage_accounts' => ['4130', '4512'],

    /** Winrate control figures (full history) — for validation after deploy. */
    'winrate_validation' => [
        'Verkooppijplijn' => ['won' => 55, 'lost' => 148, 'pct' => 27.1],
        'AFC Verkooplijn' => ['won' => 16, 'lost' => 8, 'pct' => 66.7],
    ],

];
