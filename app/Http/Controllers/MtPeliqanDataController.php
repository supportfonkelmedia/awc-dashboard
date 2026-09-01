<?php

namespace App\Http\Controllers;

use App\Services\Peliqan\PeliqanClient;
use App\Services\Peliqan\PeliqanException;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class MtPeliqanDataController extends Controller
{
    private const BUNDLES = ['cashweb', 'hubspot', 'sprinter'];

    public function __invoke(Request $request, PeliqanClient $peliqan): JsonResponse
    {
        $bundle = strtolower((string) $request->query('bundle', ''));
        if (! in_array($bundle, self::BUNDLES, true)) {
            return response()->json([
                'error' => 'Ongeldige bundle. Gebruik: cashweb, hubspot of sprinter.',
            ], 422);
        }

        $token = (string) config('peliqan.token', '');
        $url = (string) config('peliqan.mt_data_url', '');

        if ($token === '' || $url === '') {
            return response()->json([
                'error' => 'Peliqan is niet geconfigureerd (PELIQAN_JWT / PELIQAN_MT_DATA_URL).',
            ], 503);
        }

        $bookYear = (string) $request->query('book_year', (string) now()->year);
        $month = (string) $request->query('month', 'all');
        $quarter = (string) $request->query('quarter', 'all');
        $startDate = (string) $request->query('start_date', sprintf('%s-01-01', $bookYear));
        $endDate = (string) $request->query('end_date', now()->format('Y-m-d'));

        $wageAccounts = config('mt_kpi.wage_accounts', []);

        $query = array_filter([
            'bundle' => $bundle,
            'book_year' => $bookYear,
            'month' => $month,
            'quarter' => $quarter,
            'start_date' => $startDate,
            'end_date' => $endDate,
            'wage_accounts' => $wageAccounts !== [] ? json_encode($wageAccounts) : null,
        ], fn ($v) => $v !== null && $v !== '');

        $cacheKey = 'peliqan:mt:'.$bundle.':v2:'.md5(json_encode($query));
        $ttl = (int) config('peliqan.cache_ttl', 120);
        $timeout = (int) config('peliqan.timeout', 60);

        try {
            $payload = $ttl > 0
                ? Cache::remember($cacheKey, $ttl, fn () => $peliqan->fetchMt($query))
                : $peliqan->fetchMt($query);

            return response()->json($payload);
        } catch (ConnectionException $e) {
            Log::warning('Peliqan MT connection timeout', [
                'bundle' => $bundle,
                'timeout' => $timeout,
                'message' => $e->getMessage(),
            ]);

            return $this->staleOrError(
                $cacheKey,
                "Peliqan {$bundle} timeout na {$timeout}s.",
                504,
            );
        } catch (PeliqanException $e) {
            Log::warning('Peliqan MT script error', [
                'bundle' => $bundle,
                'message' => $e->getMessage(),
            ]);

            return $this->staleOrError($cacheKey, $e->getMessage(), 502);
        }
    }

    private function staleOrError(string $cacheKey, string $message, int $status): JsonResponse
    {
        $stale = Cache::get($cacheKey);
        if (is_array($stale)) {
            return response()->json([
                ...$stale,
                'meta' => [
                    ...(is_array($stale['meta'] ?? null) ? $stale['meta'] : []),
                    'stale' => true,
                    'stale_reason' => $status === 504 ? 'timeout' : 'peliqan_error',
                ],
            ]);
        }

        return response()->json(['error' => $message], $status);
    }
}
