<?php

namespace App\Console\Commands;

use App\Models\KpiDoelInvoer;
use App\Models\KpiHandmatigeInvoer;
use Illuminate\Console\Command;

class ExportKpiInvoerCommand extends Command
{
    protected $signature = 'kpi:export-invoer
                            {--pretty : JSON pretty print}
                            {--output= : Write JSON to this path instead of stdout}';

    protected $description = 'Export staging kpi_invoer rows (MariaDB) for Peliqan sync';

    public function handle(): int
    {
        $payload = [
            'exported_at' => now()->toIso8601String(),
            'source' => 'fonkel_mariadb_staging',
            'handmatig' => KpiHandmatigeInvoer::query()->orderBy('id')->get()->toArray(),
            'doelen' => KpiDoelInvoer::query()->orderBy('id')->get()->toArray(),
        ];

        $flags = $this->option('pretty') ? JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE : 0;
        $json = json_encode($payload, $flags);
        if ($json === false) {
            $this->error('JSON encode failed.');

            return self::FAILURE;
        }

        $output = (string) $this->option('output');
        if ($output !== '') {
            $dir = dirname($output);
            if (! is_dir($dir) && ! mkdir($dir, 0755, true) && ! is_dir($dir)) {
                $this->error("Cannot create directory: {$dir}");

                return self::FAILURE;
            }
            file_put_contents($output, $json);
            $this->info("Exported to {$output}");

            return self::SUCCESS;
        }

        $this->line($json);

        return self::SUCCESS;
    }
}
