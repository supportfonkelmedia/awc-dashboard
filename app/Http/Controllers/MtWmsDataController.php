<?php

namespace App\Http\Controllers;

use App\Services\Peliqan\PeliqanClient;
use App\Services\Peliqan\PeliqanException;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class MtWmsDataController extends Controller
{
    public function __invoke(PeliqanClient $peliqan): JsonResponse
    {
        $token = (string) config('peliqan.token', '');
        $url = (string) config('peliqan.awc_7t_url', '');

        if ($token === '' || $url === '') {
            return response()->json([
                'error' => '7T WMS niet geconfigureerd (PELIQAN_JWT / PELIQAN_AWC_7T_URL).',
            ], 503);
        }

        // Bump key when handler logic changes so stale SQL-error payloads are not reused.
        $cacheKey = 'peliqan:awc:7t:summary:v1';
        $ttl = (int) config('peliqan.wms_cache_ttl', 600);
        $timeout = (int) config('peliqan.wms_timeout', 120);

        try {
            $payload = $ttl > 0
                ? Cache::remember($cacheKey, $ttl, fn () => $peliqan->fetch7tWms())
                : $peliqan->fetch7tWms();

            return response()->json($payload);
        } catch (ConnectionException $e) {
            Log::warning('Peliqan WMS connection timeout', [
                'timeout' => $timeout,
                'message' => $e->getMessage(),
            ]);

            $stale = Cache::get($cacheKey);
            if (is_array($stale)) {
                return response()->json([
                    ...$stale,
                    'meta' => [
                        ...(is_array($stale['meta'] ?? null) ? $stale['meta'] : []),
                        'stale' => true,
                        'stale_reason' => 'timeout',
                    ],
                ]);
            }

            return response()->json([
                'error' => "7T WMS timeout na {$timeout}s — Peliqan/Trino reageert traag. Probeer het later opnieuw.",
            ], 504);
        } catch (PeliqanException $e) {
            $stale = Cache::get($cacheKey);
            if (is_array($stale)) {
                return response()->json([
                    ...$stale,
                    'meta' => [
                        ...(is_array($stale['meta'] ?? null) ? $stale['meta'] : []),
                        'stale' => true,
                        'stale_reason' => 'peliqan_error',
                    ],
                ]);
            }

            return response()->json(['error' => $e->getMessage()], 502);
        }
    }
}
