<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

/**
 * Detail-drills onder Churn en Winrate en het scopefilter van de drawer (handler v10).
 * De kolommen moeten gelijk blijven aan de Peliqan-views kpi_churn_klant_my_queries en
 * kpi_winrate_deal_my_queries (documentation/peliqan-sql).
 */
class KpiDrillDetailTest extends TestCase
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

    public function test_detail_views_have_the_peliqan_columns(): void
    {
        $verwacht = [
            'kpi_churn_klant' => ['scope_code', 'tegelvenster', 'vertrekdatum', 'kwartaal', 'klant', 'vertrekken_die_dag', 'bulkdag', 'icp_score', 'nu_weer_klant', 'company_id'],
            'kpi_winrate_deal' => ['scope_code', 'tegelvenster', 'deal', 'fase', 'uitkomst', 'aangemaakt', 'beslisdatum', 'beslissingen_die_dag', 'bulkdag', 'bedrag', 'eigenaar', 'deal_id'],
        ];

        $json = $this->actingAs(User::factory()->create())
            ->getJson('/kpi/peliqan/data?bundle=drill&views='.implode(',', array_keys($verwacht)))
            ->assertOk()
            ->json();

        foreach ($verwacht as $view => $kolommen) {
            $this->assertNotEmpty($json['tables'][$view], $view);
            $this->assertSame($kolommen, array_keys($json['tables'][$view][0]), $view);
        }
    }

    public function test_scope_keeps_only_the_rows_of_the_tile(): void
    {
        $json = $this->actingAs(User::factory()->create())
            ->getJson('/kpi/peliqan/data?bundle=drill&views=kpi_winrate_deal&scope='.rawurlencode('AFC - Verkooplijn'))
            ->assertOk()
            ->json();

        $scopes = array_unique(array_column($json['tables']['kpi_winrate_deal'], 'scope_code'));
        $this->assertSame(['AFC - Verkooplijn'], array_values($scopes));
    }

    public function test_scope_rejects_odd_characters(): void
    {
        $this->actingAs(User::factory()->create())
            ->getJson('/kpi/peliqan/data?bundle=drill&views=kpi_churn_klant&scope='.rawurlencode("x' OR 1=1"))
            ->assertStatus(422);
    }

    public function test_churn_and_winrate_tiles_point_at_the_detail_drills(): void
    {
        $user = User::factory()->create();

        foreach (['strategisch', 'operationeel', 'afc'] as $scherm) {
            $config = $this->actingAs($user)
                ->getJson('/kpi/peliqan/data?bundle=screen&scherm='.$scherm)
                ->assertOk()
                ->json('tegel_config');

            foreach ($config as $row) {
                if (($row['kpi_code'] ?? null) === 'churn') {
                    $this->assertStringContainsString('kpi_churn_klant', $row['drill_views'], $scherm);
                }
                if (($row['kpi_code'] ?? null) === 'winrate') {
                    $this->assertStringContainsString('kpi_winrate_deal', $row['drill_views'], $scherm);
                }
            }
        }
    }
}
