<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

/**
 * Data-integriteit: een fout of half antwoord van Peliqan mag niet een uur in de cache blijven,
 * en bij een storing tonen we het laatste volledige antwoord, gemarkeerd als verouderd.
 */
class KpiScreenCacheTest extends TestCase
{
    use RefreshDatabase;

    private const URL = 'https://peliqan.test/kpi';

    protected function setUp(): void
    {
        parent::setUp();

        config([
            'peliqan.token' => 'test-jwt',
            'peliqan.kpi_data_url' => self::URL,
            'peliqan.kpi_cache_ttl' => 3600,
            'kpi.use_fixture' => false,
            'kpi.fallback_fixture' => false,
        ]);
        Cache::flush();
    }

    private function volledig(): array
    {
        return ['bundle' => 'screen', 'scherm' => 'strategisch', 'kpi_oordeel' => [['kpi_code' => 'ebitda']], 'errors' => []];
    }

    public function test_handler_error_is_not_cached(): void
    {
        Http::fake([
            self::URL.'*' => Http::sequence()
                ->push(['error' => 'invalid_scherm'], 200)
                ->push($this->volledig(), 200),
        ]);
        $user = User::factory()->create();

        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertStatus(422);
        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')
            ->assertOk()
            ->assertJsonPath('kpi_oordeel.0.kpi_code', 'ebitda');

        Http::assertSentCount(2);
    }

    public function test_partial_answer_is_cached_only_briefly(): void
    {
        $half = [...$this->volledig(), 'errors' => [['table' => 'kpi_trend', 'error' => 'relation does not exist']]];
        Http::fake([
            self::URL.'*' => Http::sequence()->push($half, 200)->push($this->volledig(), 200),
        ]);
        $user = User::factory()->create();

        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertOk()->assertJsonCount(1, 'errors');
        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertOk()->assertJsonCount(1, 'errors');
        Http::assertSentCount(1);

        $this->travel(61)->seconds();
        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertOk()->assertJsonCount(0, 'errors');
        Http::assertSentCount(2);
    }

    public function test_truncation_warning_still_counts_as_complete(): void
    {
        $gewaarschuwd = [...$this->volledig(), 'errors' => [['view' => 'kpi_trend', 'warning' => 'truncated_to_2000_rows']]];
        Http::fake([self::URL.'*' => Http::response($gewaarschuwd, 200)]);
        $user = User::factory()->create();

        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertOk();
        $this->travel(30)->minutes();
        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertOk();

        Http::assertSentCount(1);
    }

    public function test_outage_falls_back_to_last_complete_answer_marked_stale(): void
    {
        Http::fake([
            self::URL.'*' => Http::sequence()
                ->push($this->volledig(), 200)
                ->push(['message' => 'boom'], 500),
        ]);
        $user = User::factory()->create();

        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertOk();

        $this->travel(2)->hours();
        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')
            ->assertOk()
            ->assertJsonPath('kpi_oordeel.0.kpi_code', 'ebitda')
            ->assertJsonPath('meta.stale', true)
            ->assertJsonPath('meta.stale_reason', 'peliqan_error');
    }

    public function test_outage_without_earlier_answer_returns_error(): void
    {
        Http::fake([self::URL.'*' => Http::response(['message' => 'boom'], 500)]);
        $user = User::factory()->create();

        $this->actingAs($user)->getJson('/kpi/api/screens/strategisch')->assertStatus(502);
    }
}
