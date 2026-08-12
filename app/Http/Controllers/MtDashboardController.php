<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class MtDashboardController extends Controller
{
    public function __invoke(Request $request): Response
    {
        $bookYear = (string) $request->query('book_year', (string) now()->year);
        $month = (string) $request->query('month', 'all');
        $startDate = (string) $request->query('start_date', sprintf('%s-01-01', $bookYear));
        $endDate = (string) $request->query('end_date', now()->format('Y-m-d'));

        $token = (string) config('peliqan.token', '');
        $url = (string) config('peliqan.mt_data_url', '');

        $configError = ($token === '' || $url === '')
            ? 'Peliqan is niet geconfigureerd (PELIQAN_JWT / PELIQAN_MT_DATA_URL).'
            : null;

        return Inertia::render('MtDashboard', [
            'peliqanError' => $configError,
            'filters' => [
                'book_year' => $bookYear,
                'month' => $month,
                'start_date' => $startDate,
                'end_date' => $endDate,
            ],
        ]);
    }
}
