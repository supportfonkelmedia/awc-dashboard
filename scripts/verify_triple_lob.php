<?php

require __DIR__.'/../vendor/autoload.php';
$app = require_once __DIR__.'/../bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$c = app(\App\Services\Peliqan\PeliqanClient::class);
$r = $c->fetchMt(['bundle' => 'cashweb', 'book_year' => '2025']);
$tl = $r['data']['triple_lob'] ?? null;

if (! $tl) {
    echo "MISSING triple_lob (deploy peliqan_mt_api_handler)\n";
    if (isset($r['data']['triple_lob_customers'])) {
        echo "Old triple_lob_customers still present\n";
    }
    exit(1);
}

echo 'klanten_totaal='.$tl['klanten_totaal']."\n";
echo 'in_alle_drie='.$tl['in_alle_drie']."\n";
echo 'pct_triple_lob='.$tl['pct_triple_lob']."\n";
echo 'pct_omzet='.$tl['pct_omzet_triple_lob']."\n";
echo 'controleren='.$tl['controleren_count']."\n";
echo "validation:\n";
foreach ($tl['validation'] ?? [] as $row) {
    echo '  '.$row['zekerheid'].' LOB='.$row['aantal_lob'].' n='.$row['klanten']."\n";
}
