<?php

namespace Tests\Unit;

use App\Services\Kpi\KpiFormatService;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

class KpiFormatServiceTest extends TestCase
{
    private KpiFormatService $fmt;

    protected function setUp(): void
    {
        parent::setUp();
        $this->fmt = new KpiFormatService;
    }

    /** Acceptatietest Overdracht: strategisch omzetbrug concern (juli 2026). */
    public function test_euro_mln_acceptatie_omzetbrug(): void
    {
        $this->assertSame(
            '€ 19,04 mln',
            $this->fmt->formatValue('euro', 19_040_567),
        );
    }

    public function test_euro_k_acceptatie_acc(): void
    {
        $this->assertSame(
            '€ 215k',
            $this->fmt->formatValue('euro', 214_800),
        );
    }

    #[DataProvider('deltaPctProvider')]
    public function test_pct_change_from_delta(int $delta, int $vorige, int $expected): void
    {
        $this->assertSame(
            $expected,
            $this->fmt->pctChangeFromDelta($delta, $vorige),
        );
    }

    /**
     * @return array<string, array{int, int, int}>
     */
    public static function deltaPctProvider(): array
    {
        return [
            'omzetbrug +10%' => [1_769_211, 17_271_356, 10],
            'afc -3%' => [-237_542, 7_018_690, -3],
        ];
    }
}
