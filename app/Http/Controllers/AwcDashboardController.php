<?php

namespace App\Http\Controllers;

use App\Services\Peliqan\PeliqanClient;
use App\Services\Peliqan\PeliqanException;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Inertia\Inertia;
use Inertia\Response;

class AwcDashboardController extends Controller
{
    public function __invoke(Request $request, PeliqanClient $peliqan): Response
    {
        $token = (string) config('peliqan.token', '');
        $awcUrl = (string) config('peliqan.awc_data_url', '');
        $sevenTUrl = (string) config('peliqan.awc_7t_url', '');

        $error = null;

        if ($token === '' || $awcUrl === '') {
            return Inertia::render('TeamRapportage', [
                'teamCode' => 'AWC',
                'peliqan' => null,
                'peliqanError' => 'Peliqan is niet geconfigureerd (PELIQAN_JWT / PELIQAN_AWC_DATA_URL).',
            ]);
        }

        // dw_2401 bundle (HubSpot + finance) — own cache.
        $awcData = ['hubspot' => null, 'finance' => null];
        $awcMeta = [];
        try {
            $ttl = (int) config('peliqan.cache_ttl', 120);
            $awc = $ttl > 0
                ? Cache::remember('peliqan:awc:all:v2', $ttl, fn () => $peliqan->fetchAwc(['bundle' => 'all']))
                : $peliqan->fetchAwc(['bundle' => 'all']);
            $awcData = is_array($awc['data'] ?? null) ? $awc['data'] : $awcData;
            $awcMeta = is_array($awc['meta'] ?? null) ? $awc['meta'] : [];
        } catch (PeliqanException $e) {
            $error = $e->getMessage();
        }

        // 7T WMS bundle (direct SQL Server) — own endpoint, own cache. Optional:
        // when unconfigured or failing, the page still renders dw_2401 data.
        $wmsData = null;
        $wmsMeta = ['available' => false];
        if ($sevenTUrl !== '') {
            try {
                $ttl = (int) config('peliqan.wms_cache_ttl', 600);
                $seven = $ttl > 0
                    ? Cache::remember('peliqan:awc:7t:summary:v1', $ttl, fn () => $peliqan->fetch7tWms())
                    : $peliqan->fetch7tWms();
                $wmsData = $seven['data'] ?? null;
                $metaWms = $seven['meta']['wms'] ?? null;
                if (is_array($metaWms)) {
                    $wmsMeta = $metaWms;
                }
            } catch (PeliqanException $e) {
                $wmsMeta = ['available' => false, 'probe_error' => $e->getMessage()];
            }
        }

        $payload = [
            'bundle' => 'all',
            'meta' => [
                ...$awcMeta,
                'wms' => $wmsMeta,
            ],
            'data' => [
                'wms' => $wmsData,
                'hubspot' => $awcData['hubspot'] ?? null,
                'finance' => $awcData['finance'] ?? null,
            ],
        ];

        return Inertia::render('TeamRapportage', [
            'teamCode' => 'AWC',
            'peliqan' => $payload,
            'peliqanError' => $error,
        ]);
    }
}
