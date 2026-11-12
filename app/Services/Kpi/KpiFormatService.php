<?php

namespace App\Services\Kpi;

/**
 * Server-side KPI display formatting (mirrors resources/js/utils/kpiFormat.js).
 * Used for exports, tests, and future SSR, not for live Vue tiles.
 */
class KpiFormatService
{
    public function formatValue(string $eenheid, mixed $waarde): string
    {
        if ($waarde === null || $waarde === '') {
            return '';
        }
        $n = is_numeric($waarde) ? (float) $waarde : null;
        if ($n === null) {
            return (string) $waarde;
        }

        return match ($eenheid) {
            'ratio' => $this->fmtRatio($n),
            'procent' => $this->fmtProcent($n),
            'euro' => $this->fmtEuroValue($n),
            'aantal' => $this->fmtAantal($n),
            'dagen' => $this->fmtDagen($n),
            'score' => $this->fmtScore($n),
            default => (string) $waarde,
        };
    }

    /**
     * @return array{text: string, direction: 'up'|'down'|'flat', rawDelta?: float}|null
     */
    public function formatDelta(string $eenheid, mixed $delta): ?array
    {
        if ($delta === null || $delta === '' || ! is_numeric($delta)) {
            return null;
        }
        $d = (float) $delta;
        if ($d === 0.0) {
            return ['text' => 'gelijk', 'direction' => 'flat'];
        }

        $sign = $d > 0 ? '+' : '−';
        $abs = abs($d);

        return match ($eenheid) {
            'ratio' => [
                'text' => $sign.$this->fmtRatio($abs).' t.o.v. vorige maand',
                'direction' => $d > 0 ? 'up' : 'down',
            ],
            'procent' => [
                'text' => $sign.rtrim($this->fmtProcent($abs), '%').' pp t.o.v. vorige maand',
                'direction' => $d > 0 ? 'up' : 'down',
            ],
            'euro' => [
                'text' => $sign.ltrim($this->fmtEuroValue($abs), '−'),
                'direction' => $d > 0 ? 'up' : 'down',
                'rawDelta' => $d,
            ],
            'aantal' => [
                'text' => $sign.$this->fmtAantal($abs),
                'direction' => $d > 0 ? 'up' : 'down',
                'rawDelta' => $d,
            ],
            'dagen' => [
                'text' => $sign.number_format($abs, 1, ',', '.').' dagen',
                'direction' => $d > 0 ? 'up' : 'down',
            ],
            'score' => [
                'text' => $sign.$this->fmtScore($abs),
                'direction' => $d > 0 ? 'up' : 'down',
            ],
            default => [
                'text' => $sign.(string) $abs,
                'direction' => $d > 0 ? 'up' : 'down',
            ],
        };
    }

    public function pctChangeFromDelta(mixed $delta, mixed $waardeVorige): ?int
    {
        if ($delta === null || $waardeVorige === null || ! is_numeric($delta) || ! is_numeric($waardeVorige)) {
            return null;
        }
        $prev = (float) $waardeVorige;
        if ($prev === 0.0) {
            return null;
        }

        return (int) round(((float) $delta / abs($prev)) * 100);
    }

    public function fmtRatio(float $n): string
    {
        return number_format($n, 2, ',', '.');
    }

    public function fmtProcent(float $n): string
    {
        return number_format($n, 1, ',', '.').'%';
    }

    public function fmtEuroValue(float $v): string
    {
        $sign = $v < 0 ? '−' : '';
        $abs = abs($v);

        if ($abs >= 1_000_000) {
            return $sign.'€ '.number_format($abs / 1_000_000, 2, ',', '.').' mln';
        }
        if ($abs >= 10_000) {
            return $sign.'€ '.number_format((int) round($abs / 1000), 0, ',', '.').'k';
        }

        return $sign.'€ '.number_format((int) round($abs), 0, ',', '.');
    }

    public function fmtAantal(float $n): string
    {
        return number_format((int) round($n), 0, ',', '.');
    }

    public function fmtDagen(float $n): string
    {
        return number_format($n, 1, ',', '.').' dagen';
    }

    public function fmtScore(float $n): string
    {
        return number_format((int) round($n), 0, ',', '.');
    }
}
