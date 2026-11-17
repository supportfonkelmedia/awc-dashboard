<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\Client\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

/**
 * Laravel-kant van de drill-route met echte Peliqan-antwoorden. De payloads hieronder zijn
 * letterlijk wat handler v10 (app 17395) op 2026-11-12 20:05 UTC teruggaf in de live runtime
 * (tijdelijke e2e-app, 48 aanroepen, 0 fouten), alleen klant- en dealnamen zijn vervangen.
 * Getest: validatie, scope en views gaan mee naar Peliqan, de JWT-header staat erop, en het
 * antwoord (tables + table_meta) komt ongewijzigd bij de drawer aan.
 */
class KpiDrillPeliqanRouteTest extends TestCase
{
    use RefreshDatabase;

    private const URL = 'https://peliqan.test/kpi/data';

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

    /** @return array<string, mixed> */
    private function winrateAfcAntwoord(): array
    {
        $deal = fn (string $naam, string $aangemaakt, string $id) => [
            'scope_code' => 'AFC - Verkooplijn', 'tegelvenster' => 'telt mee', 'deal' => $naam,
            'fase' => 'Verloren', 'uitkomst' => 'verloren', 'aangemaakt' => $aangemaakt,
            'beslisdatum' => '2026-11-03', 'beslissingen_die_dag' => 9, 'bulkdag' => false,
            'bedrag' => null, 'eigenaar' => null, 'deal_id' => $id,
        ];

        return [
            'bundle' => 'drill',
            'views' => ['kpi_winrate_deal', 'kpi_winrate_maand'],
            'tables' => [
                'kpi_winrate_deal' => [
                    $deal('AWC → AFC | Deal A', '2026-10-06', '525220220138'),
                    $deal('AWC → AFC | Deal B', '2026-05-11', '502458473697'),
                    $deal('AWC → AFC | Deal C', '2026-03-19', '494625047751'),
                ],
                'kpi_winrate_maand' => [
                    ['pipeline' => 'AFC - Verkooplijn', 'peildatum' => '2026-11-12', 'soort' => 'vandaag', 'aangemaakt' => 166, 'gewonnen' => 0, 'verloren' => 6, 'gewonnen_alleen_hubspot_vlag' => 0, '_pq_materialized_at' => '2026-11-12T19:50:30.510'],
                ],
            ],
            'table_meta' => [
                'kpi_winrate_deal' => ['row_count' => 3, 'truncated' => true, 'total_count' => 237, 'limit' => 3, 'ordered' => true, 'filters' => ['scope' => 'AFC - Verkooplijn']],
                'kpi_winrate_maand' => ['row_count' => 1, 'truncated' => false, 'total_count' => 1, 'limit' => 3, 'ordered' => true, 'filters' => ['scope' => 'AFC - Verkooplijn']],
            ],
            'errors' => [['view' => 'kpi_winrate_deal', 'warning' => 'truncated_to_3_rows']],
            'meta' => ['warehouse' => 'dw_2401', 'handler_version' => '2026-11-12-kpi-v10-drill-detail-scope', 'limit' => 3, 'filters' => ['scope' => 'AFC - Verkooplijn']],
        ];
    }

    /** @return array<string, mixed> */
    private function ebitdaAwcAntwoord(): array
    {
        return [
            'bundle' => 'drill',
            'views' => ['kpi_ebitda_maand', 'kpi_kosten_maand'],
            'tables' => [
                'kpi_ebitda_maand' => [
                    ['scope_code' => 'alaw', 'scope_label' => 'AWC', 'maand' => '2026-10-01', 'omzet' => 1348311.0, 'ebitda' => 225410.0, 'ebitda_marge_pct' => 16.7, 'ebitda_12m' => 619670.0, 'maanden_in_12m' => 12, 'ebitda_jaar_tot_nu' => 665769.0, 'afgesloten' => false, '_pq_materialized_at' => '2026-11-12T19:51:29.390'],
                ],
                'kpi_kosten_maand' => [
                    ['scope_code' => 'alaw', 'scope_label' => 'AWC', 'maand' => '2026-12-01', 'groep' => '2 Inkoop en directe kosten', 'bedrag' => 262.0, 'afgesloten' => false, '_pq_materialized_at' => '2026-11-12T19:51:36.136'],
                ],
            ],
            'table_meta' => [
                'kpi_ebitda_maand' => ['row_count' => 1, 'truncated' => true, 'total_count' => 36, 'limit' => 1, 'ordered' => true, 'filters' => ['scope' => 'alaw']],
                'kpi_kosten_maand' => ['row_count' => 1, 'truncated' => true, 'total_count' => 249, 'limit' => 1, 'ordered' => true, 'filters' => ['scope' => 'alaw']],
            ],
            'errors' => [],
            'meta' => ['warehouse' => 'dw_2401', 'handler_version' => '2026-11-12-kpi-v10-drill-detail-scope', 'limit' => 1, 'filters' => ['scope' => 'alaw']],
        ];
    }

    public function test_drawer_request_reaches_peliqan_with_scope_views_and_jwt(): void
    {
        Http::fake([self::URL.'*' => Http::response($this->winrateAfcAntwoord(), 200)]);

        $json = $this->actingAs(User::factory()->create())
            ->getJson('/kpi/peliqan/data?'.http_build_query([
                'bundle' => 'drill',
                'views' => 'kpi_winrate_deal,kpi_winrate_maand',
                'scope' => 'AFC - Verkooplijn',
            ]))
            ->assertOk()
            ->json();

        Http::assertSent(function (Request $r) {
            parse_str((string) parse_url($r->url(), PHP_URL_QUERY), $q);

            return str_starts_with($r->url(), self::URL)
                && $r->hasHeader('Authorization', 'JWT test-jwt')
                && ($q['bundle'] ?? null) === 'drill'
                && ($q['views'] ?? null) === 'kpi_winrate_deal,kpi_winrate_maand'
                && ($q['scope'] ?? null) === 'AFC - Verkooplijn';
        });

        $this->assertSame($this->winrateAfcAntwoord()['tables'], $json['tables']);
        $this->assertSame(237, $json['table_meta']['kpi_winrate_deal']['total_count']);
        $this->assertSame(['AFC - Verkooplijn'], array_values(array_unique(array_column($json['tables']['kpi_winrate_deal'], 'scope_code'))));
    }

    public function test_scope_is_part_of_the_cache_key(): void
    {
        Http::fake([
            self::URL.'*' => function (Request $r) {
                parse_str((string) parse_url($r->url(), PHP_URL_QUERY), $q);

                return Http::response(($q['scope'] ?? '') === 'alaw' ? $this->ebitdaAwcAntwoord() : $this->winrateAfcAntwoord(), 200);
            },
        ]);
        $user = User::factory()->create();

        $a = $this->actingAs($user)->getJson('/kpi/peliqan/data?bundle=drill&views=kpi_ebitda_maand,kpi_kosten_maand&scope=alaw')->assertOk()->json();
        $b = $this->actingAs($user)->getJson('/kpi/peliqan/data?bundle=drill&views=kpi_ebitda_maand,kpi_kosten_maand&scope=pgl1')->assertOk()->json();

        // Twee scopes, twee aanroepen: AWC mag nooit uit de cache van AFC komen (of andersom).
        Http::assertSentCount(2);
        $this->assertSame('alaw', $a['tables']['kpi_ebitda_maand'][0]['scope_code']);
        $this->assertArrayHasKey('kpi_winrate_deal', $b['tables']);
    }
    /** @return array<string, mixed> */
    private function afcLiveAntwoord(int $zendingen): array
    {
        return [
            'bundle' => 'drill',
            'views' => ['kpi_afc_zending_maand', 'kpi_afc_resultaat_maand'],
            'tables' => [
                'kpi_afc_zending_maand' => [
                    ['maand' => '2026-11-01', 'jaar' => 2026, 'maandnummer' => 11, 'modaliteit' => 'Weg', 'richting' => 'Export', 'ytd_venster' => true, 'zendingen' => $zendingen, 'zendingen_open' => 12, 'omzet' => 51234.5, 'omzet_incl_invoerrechten' => 51234.5, 'marge' => 10234.1],
                ],
                'kpi_afc_resultaat_maand' => [],
            ],
            'table_meta' => [],
            'errors' => [],
            'meta' => [
                'warehouse' => 'dw_2401',
                'handler_version' => '2026-11-16-kpi-v11-afc-sprinter-live',
                'limit' => 5000,
                'filters' => [],
                'sprinter_live' => ['status' => 'ok', 'opgehaald_om' => '2026-11-16T11:48:51.885Z', 'nachtsync_om' => '2026-11-16T01:31:35.912Z', 'opgehaald' => 500, 'nieuw' => 0, 'gewijzigd' => 1, 'duur_ms' => 8183, 'melding' => null, 'interval_s' => 60],
            ],
        ];
    }

    public function test_live_afc_drill_skips_the_hour_cache(): void
    {
        $n = 0;
        Http::fake([self::URL.'*' => function () use (&$n) {
            $n++;

            return Http::response($this->afcLiveAntwoord(100 + $n), 200);
        }]);
        $user = User::factory()->create();
        $url = '/kpi/peliqan/data?bundle=drill&views=kpi_afc_zending_maand,kpi_afc_resultaat_maand&limit=5000';

        $a = $this->actingAs($user)->getJson($url)->assertOk()->json();
        $b = $this->actingAs($user)->getJson($url)->assertOk()->json();

        // Elke keer naar Peliqan: de handler bepaalt zelf hoe vaak Sprinter wordt opgehaald (1x per minuut).
        Http::assertSentCount(2);
        $this->assertSame(101, $a['tables']['kpi_afc_zending_maand'][0]['zendingen']);
        $this->assertSame(102, $b['tables']['kpi_afc_zending_maand'][0]['zendingen']);
        $this->assertSame('ok', $b['meta']['sprinter_live']['status']);
    }

    public function test_non_live_drill_still_uses_the_hour_cache(): void
    {
        Http::fake([self::URL.'*' => Http::response($this->ebitdaAwcAntwoord(), 200)]);
        $user = User::factory()->create();
        $url = '/kpi/peliqan/data?bundle=drill&views=kpi_ebitda_maand,kpi_kosten_maand&scope=alaw';

        $this->actingAs($user)->getJson($url)->assertOk();
        $this->actingAs($user)->getJson($url)->assertOk();

        Http::assertSentCount(1);
    }

    public function test_live_afc_drill_falls_back_to_last_good_answer_on_outage(): void
    {
        $n = 0;
        Http::fake([self::URL.'*' => function () use (&$n) {
            $n++;

            return $n === 1
                ? Http::response($this->afcLiveAntwoord(101), 200)
                : Http::response(['error' => 'storing'], 500);
        }]);
        $user = User::factory()->create();
        $url = '/kpi/peliqan/data?bundle=drill&views=kpi_afc_zending_maand,kpi_afc_resultaat_maand&limit=5000';

        $this->actingAs($user)->getJson($url)->assertOk();
        $json = $this->actingAs($user)->getJson($url)->assertOk()->json();

        Http::assertSentCount(2);
        $this->assertSame(101, $json['tables']['kpi_afc_zending_maand'][0]['zendingen']);
        $this->assertTrue($json['meta']['stale']);
    }
}
