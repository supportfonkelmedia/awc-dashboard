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
$c = app(\App\Services\Peliqan\PeliqanClient::class);
$r = $c->fetch7tWms(['year' => (string) $year]);
$d2s = $r['data']['dock_to_stock'] ?? null;

if (! $d2s) {
    echo "MISSING dock_to_stock (deploy peliqan_7t_api_handler deel 3)\n";
    $err = $r['data']['errors']['dock_to_stock'] ?? null;
    if ($err) {
        echo "error: {$err}\n";
    }
    exit(1);
}

echo "year={$d2s['year']}\n";
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
        echo "\nWARN: cijfers wijken af van briefing (~6765 orders, 74.6%)\n";
        exit(2);
    }
    echo "\nOK: binnen verwachte band voor 2026\n";
}
