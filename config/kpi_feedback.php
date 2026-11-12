<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Feedback admins
    |--------------------------------------------------------------------------
    |
    | Comma-separated email addresses that may open the feedback overview
    | (/kpi/feedback) and change statuses. Everyone who is logged in can
    | submit feedback; only these addresses see what others submitted.
    |
    */
    'admin_emails' => array_values(array_unique(array_filter(array_map(
        static fn (string $email): string => strtolower(trim($email)),
        explode(',', (string) env('KPI_FEEDBACK_ADMINS', '')),
    )))),

];
