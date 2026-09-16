<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Registration allow list
    |--------------------------------------------------------------------------
    |
    | Comma-separated email addresses that may self-register via /register.
    | When enabled with an empty list, registration is blocked for everyone.
    | Set REGISTRATION_ALLOWLIST_ENABLED=false to allow open signup (e.g. local).
    |
    */
    'allowlist_enabled' => env('REGISTRATION_ALLOWLIST_ENABLED', true),

    'allowed_emails' => array_values(array_unique(array_filter(array_map(
        static fn (string $email): string => strtolower(trim($email)),
        explode(',', (string) env('REGISTRATION_ALLOWED_EMAILS', '')),
    )))),

];
