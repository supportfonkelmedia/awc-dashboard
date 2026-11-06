<?php

namespace App\Services\Kpi;

use App\Http\Controllers\KpiDashboardController;
use App\Services\Peliqan\PeliqanClient;
use App\Services\Peliqan\PeliqanException;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class KpiScreenService
{
    private const BUNDLES = ['screen', 'controles', 'drill', 'registry'];

    public function __construct(
        protected PeliqanClient $peliqan,
        protected KpiScreenFixtureProvider $fixtures,
    ) {}

    public function usesFixture(): bool
    {
        if (config('kpi.use_fixture')) {
            return true;
        }

        if (! config('kpi.fallback_fixture')) {
            return false;
        }

        return $this->configurationError() !== null;
    }

    public function configurationError(): ?string
    {
        $token = (string) config('peliqan.token', '');
        $url = (string) config('peliqan.kpi_data_url', '');

        if ($token === '' || $url === '') {
            return 'Peliqan KPI is niet geconfigureerd (PELIQAN_JWT / PELIQAN_KPI_DATA_URL).';
        }

        return null;
    }

    /**
     * @param  array<string, scalar|null>  $query
     * @return array{payload: array<string, mixed>|null, status: int, error: string|null}
     */
    public function fetch(array $query): array
    {
        if ($this->usesFixture()) {
            $payload = $this->fixtures->bundle($query);
            if ($payload === null) {
                return [
                    'payload' => ['error' => 'invalid fixture request'],
                    'status' => 422,
                    'error' => 'invalid fixture request',
                ];
            }

            return ['payload' => $payload, 'status' => 200, 'error' => null];
        }

        if ($err = $this->configurationError()) {
            return ['payload' => null, 'status' => 503, 'error' => $err];
        }

        $bundle = strtolower((string) ($query['bundle'] ?? 'screen'));
        if (! in_array($bundle, self::BUNDLES, true)) {
            return [
                'payload' => ['error' => 'invalid bundle'],
                'status' => 422,
                'error' => 'invalid bundle',
            ];
        }

        if ($bundle === 'screen') {
            $scherm = strtolower((string) ($query['scherm'] ?? ''));
            if ($scherm === '' || ! in_array($scherm, KpiDashboardController::SCREENS, true)) {
                return [
                    'payload' => ['error' => 'scherm is required when bundle=screen.'],
                    'status' => 422,
                    'error' => 'scherm is required when bundle=screen.',
                ];
            }
        }

        if ($bundle === 'drill' && empty($query['views'])) {
            return [
                'payload' => ['error' => 'views is required when bundle=drill.'],
                'status' => 422,
                'error' => 'views is required when bundle=drill.',
            ];
        }

        $filtered = array_filter(
            $query,
            fn ($v, $k) => in_array($k, ['bundle', 'scherm', 'views', 'limit'], true)
                && $v !== null && $v !== '',
            ARRAY_FILTER_USE_BOTH,
        );

        $cacheKey = 'peliqan:kpi:'.$bundle.':v1:'.md5(json_encode($filtered));
        $ttl = (int) config('peliqan.kpi_cache_ttl', 3600);
        $timeout = (int) config('peliqan.timeout', 60);

        try {
            if ($ttl > 0) {
                $cached = Cache::get($cacheKey);
                if ($cached !== null) {
                    if (config('peliqan.http_log') && config('peliqan.http_log_cache_hits')) {
                        Log::channel('peliqan')->debug('Peliqan KPI cache hit (no HTTP request)', [
                            'cache_key' => $cacheKey,
                            'request_query' => $filtered,
                            'ttl_seconds' => $ttl,
                        ]);
                    }
                    $payload = $cached;
                } else {
                    $payload = Cache::remember($cacheKey, $ttl, fn () => $this->peliqan->fetchKpi($filtered));
                }
            } else {
                $payload = $this->peliqan->fetchKpi($filtered);
            }

            if (isset($payload['error']) && is_string($payload['error'])) {
                return ['payload' => $payload, 'status' => 422, 'error' => $payload['error']];
            }

            return ['payload' => $payload, 'status' => 200, 'error' => null];
        } catch (ConnectionException $e) {
            Log::warning('Peliqan KPI connection timeout', [
                'bundle' => $bundle,
                'timeout' => $timeout,
                'message' => $e->getMessage(),
            ]);

            return $this->staleOrError($cacheKey, "Peliqan KPI {$bundle} timeout na {$timeout}s.", 504);
        } catch (PeliqanException $e) {
            Log::warning('Peliqan KPI script error', [
                'bundle' => $bundle,
                'message' => $e->getMessage(),
            ]);

            return $this->staleOrError($cacheKey, $e->getMessage(), 502);
        }
    }

    /**
     * @return array{payload: array<string, mixed>|null, status: int, error: string|null}
     */
    private function staleOrError(string $cacheKey, string $message, int $status): array
    {
        $stale = Cache::get($cacheKey);
        if (is_array($stale)) {
            return [
                'payload' => [
                    ...$stale,
                    'meta' => [
                        ...(is_array($stale['meta'] ?? null) ? $stale['meta'] : []),
                        'stale' => true,
                        'stale_reason' => $status === 504 ? 'timeout' : 'peliqan_error',
                    ],
                ],
                'status' => 200,
                'error' => null,
            ];
        }

        return ['payload' => ['error' => $message], 'status' => $status, 'error' => $message];
    }
}
