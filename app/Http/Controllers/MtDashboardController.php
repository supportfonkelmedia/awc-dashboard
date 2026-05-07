<?php

namespace App\Http\Controllers;

use App\Services\Peliqan\PeliqanClient;
use App\Services\Peliqan\PeliqanException;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Inertia\Inertia;
use Inertia\Response;

class MtDashboardController extends Controller
{
    public function __invoke(Request $request, PeliqanClient $peliqan): Response
    {
        $bookYear = (string) $request->query('book_year', (string) now()->year);
        $month = (string) $request->query('month', 'all');
        $startDate = (string) $request->query('start_date', sprintf('%s-01-01', $bookYear));
        $endDate = (string) $request->query('end_date', now()->format('Y-m-d'));

        $query = array_filter([
            'bundle' => 'all',
            'book_year' => $bookYear,
            'month' => $month,
            'start_date' => $startDate,
            'end_date' => $endDate,
        ], fn ($v) => $v !== null && $v !== '');

        $cacheKey = 'peliqan:mt:'.md5(json_encode($query));

        $error = null;
        $payload = null;

        try {
            $token = (string) config('peliqan.token', '');
            $url = (string) config('peliqan.mt_data_url', '');
            if ($token === '' || $url === '') {
                $error = 'Peliqan is niet geconfigureerd (PELIQAN_JWT / PELIQAN_MT_DATA_URL).';
            } else {
                $ttl = (int) config('peliqan.cache_ttl', 120);
                $payload = $ttl > 0
                    ? Cache::remember($cacheKey, $ttl, fn () => $peliqan->fetchMt($query))
                    : $peliqan->fetchMt($query);
            }
        } catch (PeliqanException $e) {
            $error = $e->getMessage();
        }

        return Inertia::render('MtDashboard', [
            'peliqan' => $payload,
            'peliqanError' => $error,
            'filters' => [
                'book_year' => $bookYear,
                'month' => $month,
                'start_date' => $startDate,
                'end_date' => $endDate,
            ],
        ]);
    }
}
