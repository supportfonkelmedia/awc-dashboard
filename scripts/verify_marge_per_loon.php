<?php

require __DIR__.'/../vendor/autoload.php';
$app = require_once __DIR__.'/../bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$c = app(\App\Services\Peliqan\PeliqanClient::class);
$r = $c->fetchMt(['bundle' => 'cashweb', 'book_year' => '2025']);

echo 'top_keys: '.implode(', ', array_keys($r))."\n";
echo 'data_keys: '.implode(', ', array_keys($r['data'] ?? []))."\n";
$cw = $r['data']['cashweb'] ?? $r['data'] ?? $r['cashweb'] ?? null;
if (! is_array($cw)) {
    echo "no cashweb bundle\n";
    echo json_encode(array_keys($r), JSON_PRETTY_PRINT)."\n";
    if (isset($r['error'])) {
        echo 'error: '.$r['error']."\n";
    }
    exit(1);
}

echo 'cashweb_keys: '.implode(', ', array_keys($cw))."\n";
$mpl = $cw['marge_per_loon'] ?? null;

if (! $mpl) {
    echo "MISSING marge_per_loon\n";
    exit(1);
}

echo 'entities='.count($mpl['entities'] ?? [])."\n";
echo 'totals_kpi='.($mpl['totals']['kpi'] ?? 'null')."\n";
foreach ($mpl['entities'] ?? [] as $e) {
    echo ($e['label'] ?? '?').' kpi='.($e['kpi'] ?? 'null').' months='.count($e['months'] ?? [])."\n";
}
