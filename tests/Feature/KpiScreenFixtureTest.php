<?php

namespace Tests\Feature;

use App\Models\User;
use App\Services\Kpi\KpiFormatService;
use App\Services\Kpi\KpiScreenFixtureProvider;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class KpiScreenFixtureTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        config([
            'kpi.use_fixture' => true,
            'kpi.fallback_fixture' => false,
            'peliqan.token' => '',
            'peliqan.kpi_data_url' => '',
        ]);
    }

    public function test_fixture_screen_api_returns_acceptatie_baseline(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->getJson('/kpi/api/screens/strategisch')
            ->assertOk()
            ->assertJsonPath('meta.fixture', true)
            ->assertJsonPath('controles_summary.fout', 1)
            // Volume Sprinter3000 is ok sinds de sync op sprinter_api (12-11-2026).
            ->assertJsonPath('controles_summary.let_op', 1)
            ->assertJsonPath('controles_summary.ok', 12);
    }

    public function test_fixture_omzetbrug_formats_like_acceptatie(): void
    {
        $provider = new KpiScreenFixtureProvider;
        $payload = $provider->screen('strategisch');
        $this->assertNotNull($payload);

        $oordeel = collect($payload['kpi_oordeel'] ?? [])
            ->first(fn ($r) => ($r['kpi_code'] ?? '') === 'omzet_brug' && ($r['scope_code'] ?? '') === 'concern');

        $this->assertNotNull($oordeel);
        $fmt = new KpiFormatService;

        $this->assertSame(
            '€ 19,04 mln',
            $fmt->formatValue('euro', $oordeel['waarde']),
        );
    }
}
