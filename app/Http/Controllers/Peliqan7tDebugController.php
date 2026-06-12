<?php

namespace App\Http\Controllers;

use App\Services\Peliqan\PeliqanClient;
use App\Services\Peliqan\PeliqanException;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

/**
 * Simple debug page for the direct-SQL 7T WMS endpoint.
 * The browser calls `call()` (uncached) so ?debug= and ?wms_part= pass straight
 * through to the Peliqan handler.
 */
class Peliqan7tDebugController extends Controller
{
    public function index(): Response
    {
        $token = (string) config('peliqan.token', '');
        $url = (string) config('peliqan.awc_7t_url', '');

        return Inertia::render('Debug/Peliqan7t', [
            'config' => [
                'jwt_set' => $token !== '',
                'url_set' => $url !== '',
                'url_host' => $this->safeHost($url),
            ],
        ]);
    }

    public function call(Request $request, PeliqanClient $peliqan): JsonResponse
    {
        $token = (string) config('peliqan.token', '');
        $url = (string) config('peliqan.awc_7t_url', '');

        if ($token === '' || $url === '') {
            return response()->json([
                'error' => '7T niet geconfigureerd (PELIQAN_JWT / PELIQAN_AWC_7T_URL).',
            ], 503);
        }

        $query = array_filter([
            'lookback' => (string) $request->query('lookback', ''),
            'wms_part' => (string) $request->query('wms_part', ''),
            'sample' => (string) $request->query('sample', ''),
        ], fn ($v) => $v !== '');

        $startedAt = microtime(true);

        try {
            $payload = $peliqan->fetch7tWms($query);

            return response()->json([
                'ok' => true,
                'elapsed_ms' => (int) round((microtime(true) - $startedAt) * 1000),
                'payload' => $payload,
            ]);
        } catch (ConnectionException $e) {
            $timeout = (int) config('peliqan.wms_timeout', 120);

            return response()->json([
                'ok' => false,
                'error' => "Timeout na {$timeout}s — Peliqan reageert traag.",
            ], 504);
        } catch (PeliqanException $e) {
            return response()->json([
                'ok' => false,
                'error' => $e->getMessage(),
                'payload' => $e->payload,
            ], 502);
        }
    }

    protected function safeHost(string $url): ?string
    {
        $host = parse_url($url, PHP_URL_HOST);

        return is_string($host) && $host !== '' ? $host : null;
    }
}
