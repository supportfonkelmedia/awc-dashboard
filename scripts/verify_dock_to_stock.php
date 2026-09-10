<?php

/**
 * Validate Dock-to-Stock (Brief Fonkel deel 3) against Peliqan 7T handler.
 *
 * Expected control figures (whole 2026, stand 3 sep 2026):
 *   measurable ~6765, within_24h ~5049, pct ~74.6%
 */

require __DIR__.'/../vendor/autoload.php';
$app = require_once __DIR__.'/../bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$year = (int) ($argv[1] ?? 2026);
$probe = in_array('--probe', $argv, true);
$c = app(\App\Services\Peliqan\PeliqanClient::class);
$url = (string) config('peliqan.awc_7t_url', '');
$wmsTimeout = (int) config('peliqan.wms_timeout', 300);

echo 'configured_url='.($url !== '' ? $url : '(empty — set PELIQAN_AWC_7T_URL)')."\n";
echo "wms_timeout={$wmsTimeout}s\n";

$query = ['year' => (string) $year];
if ($probe) {
    $query['dock_probe'] = '1';
} else {
    // Skip occupancy/accuracy round trip — faster validation of Dock-to-Stock only.
    $query['dock_only'] = '1';
}

try {
    $r = $c->fetch7tWms($query);
} catch (\Illuminate\Http\Client\ConnectionException $e) {
    echo "\nTIMEOUT: Peliqan did not respond within {$wmsTimeout}s.\n";
    echo "Dock-to-Stock uses Trino over ~6k rows — this can take 1–3 minutes on first run.\n";
    echo "→ Set PELIQAN_WMS_TIMEOUT=300 (or 600) in .env, then: php artisan config:clear\n";
    if ($probe) {
        echo "→ Or run without --probe (uses dock_only=1, 2 Trino queries).\n";
    }
    exit(1);
} catch (\App\Services\Peliqan\PeliqanException $e) {
    echo "Peliqan HTTP/script error: {$e->getMessage()}\n";
    exit(1);
}

$data = $r['data'] ?? [];
$meta = $r['meta'] ?? [];

if ($probe) {
    echo "dock_probe steps:\n";
    foreach ($data['steps'] ?? [] as $step) {
        $ok = ($step['ok'] ?? false) ? 'OK' : 'FAIL';
        $err = $step['error'] ?? '';
        echo "  {$step['step']}: {$ok} ({$step['ms']}ms)".($err ? " — {$err}" : '')."\n";
        if (! empty($step['sample'])) {
            echo '    sample: '.json_encode($step['sample'])."\n";
        }
    }
    if (! empty($data['hint'])) {
        echo "hint: {$data['hint']}\n";
    }
}

$handlerVersion = $data['handler_version'] ?? $meta['handler_version'] ?? '?';
$fetchDb = $meta['warehouses']['wms_db'] ?? $data['fetch_db'] ?? '?';
$dockSource = $data['dock_to_stock']['source'] ?? $data['source'] ?? '?';

echo "handler_version={$handlerVersion}\n";
echo "dock_source={$dockSource}\n";
echo 'wms_available='.(($data['wms_available'] ?? false) ? 'true' : 'false')."\n";
echo "fetch_db={$fetchDb}\n";

if (! empty($data['query_stats']['dock_to_stock_ms'])) {
    echo 'dock_to_stock_ms='.$data['query_stats']['dock_to_stock_ms']."\n";
}

if (! empty($data['errors']) && is_array($data['errors'])) {
    echo "errors:\n";
    foreach ($data['errors'] as $key => $msg) {
        if ($msg) {
            echo "  {$key}: {$msg}\n";
        }
    }
}

$d2s = $data['dock_to_stock'] ?? null;

if (! $d2s) {
    echo "\nMISSING dock_to_stock\n";
    if ($handlerVersion === '?' || ! str_contains((string) $handlerVersion, 'dock-to-stock-v')) {
        echo "→ Redeploy documentation/peliqan_7t_api_handler.py in Peliqan (expect v4+).\n";
    }
    if (! empty($data['errors']['dock_to_stock'])) {
        echo "→ php artisan cache:clear && retry\n";
        echo "→ Quick connectivity check: php scripts/verify_dock_to_stock.php 2026 --probe\n";
    }
    exit(1);
}

echo "\nyear={$d2s['year']}\n";
echo 'total_unloaded='.($d2s['total_unloaded'] ?? '?')."\n";
echo 'measurable_orders='.($d2s['measurable_orders'] ?? '?')."\n";
echo 'within_24h='.($d2s['within_24h'] ?? '?')."\n";
echo 'pct_within_24u='.($d2s['pct_within_24h'] ?? '?')."\n";
echo 'median_hours='.($d2s['median_hours'] ?? '?')."\n";
echo 'coverage_pct='.($d2s['coverage_pct'] ?? '?')."\n";
echo "monthly:\n";
foreach ($d2s['monthly'] ?? [] as $row) {
    echo '  m='.$row['month'].' pct='.$row['pct_within_24h'].' n='.$row['orders']."\n";
}

if ($year === 2026) {
    $pct = (float) ($d2s['pct_within_24h'] ?? 0);
    $meas = (int) ($d2s['measurable_orders'] ?? 0);
    if ($meas < 6500 || $meas > 7000 || $pct < 70 || $pct > 80) {
        echo "\nWARN: figures differ from briefing (~6765 orders, 74.6%)\n";
        exit(2);
    }
    echo "\nOK: within expected range for 2026\n";
}
