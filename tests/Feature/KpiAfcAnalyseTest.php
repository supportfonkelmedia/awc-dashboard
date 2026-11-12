<?php

namespace Tests\Feature;

use App\Models\User;
use App\Services\Kpi\AfcAnalyseFixture;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class KpiAfcAnalyseTest extends TestCase
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

    public function test_guest_is_redirected_to_login(): void
    {
        $this->get('/kpi/afc/analyse')->assertRedirect('/login');
    }

    public function test_page_renders_with_reference_date(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->get('/kpi/afc/analyse')
            ->assertOk()
            ->assertInertia(fn ($page) => $page
                ->component('Kpi/AfcAnalyse')
                ->where('kpiUsesFixture', true)
                ->where('vandaag', AfcAnalyseFixture::VANDAAG));
    }

    public function test_drill_returns_every_afc_view_with_the_peliqan_columns(): void
    {
        $user = User::factory()->create();

        $verwacht = [
            'kpi_afc_zending_maand' => ['maand', 'jaar', 'maandnummer', 'modaliteit', 'richting', 'ytd_venster', 'zendingen', 'zendingen_open', 'omzet', 'omzet_incl_invoerrechten', 'marge'],
            'kpi_afc_eigenaar_maand' => ['maand', 'jaar', 'eigenaar', 'afdeling', 'richting', 'ytd_venster', 'zendingen', 'omzet', 'marge'],
            'kpi_afc_klant_jaar' => ['klantgroep_id', 'klant', 'debiteurnummer', 'jaar', 'richting', 'modaliteit', 'ytd_venster', 'zendingen', 'omzet', 'marge'],
            'kpi_afc_klant' => ['klant_id', 'klant', 'klantgroep_id', 'debiteurnummer', 'klantstatus', 'eerste_zending', 'laatste_zending', 'dagen_sinds_laatste_zending', 'zendingen_totaal', 'zendingen_12m', 'omzet_12m', 'marge_12m', 'omzet_vorige_12m', 'marge_vorige_12m', 'modaliteiten_12m', 'eigenaren_12m', 'nieuwe_dienst_dit_jaar'],
            'kpi_afc_klant_retentie_jaar' => ['jaar', 'actieve_klanten', 'behouden', 'weggevallen', 'nieuw', 'teruggekeerd', 'met_1_zending', 'actief_vorig_jaar', 'omzet_weggevallen_vorig_jaar', 'omzet_nieuwe_klanten', 'retentie_pct', 'churn_pct', 'lopend_jaar'],
            'kpi_afc_resultaat_maand' => ['periode_id', 'boekjaar', 'maandnummer', 'maand', 'omzet', 'invoerrechten_doorbelast', 'omzet_incl_invoerrechten', 'btw_verkoop', 'kostprijs', 'kostprijs_sim_cargo', 'kostprijs_svz', 'brutomarge', 'brutomarge_pct', 'bedrijfskosten', 'resultaat_humber', 'resultaat_voor_belasting', 'vennootschapsbelasting', 'resultaat_na_belasting', 'periode_afwijkend'],
        ];

        $json = $this->actingAs($user)
            ->getJson('/kpi/peliqan/data?bundle=drill&views='.implode(',', array_keys($verwacht)).'&limit=5000')
            ->assertOk()
            ->json();

        foreach ($verwacht as $view => $kolommen) {
            $this->assertNotEmpty($json['tables'][$view], $view);
            $this->assertSame($kolommen, array_keys($json['tables'][$view][0]), $view);
            $this->assertLessThanOrEqual(5000, count($json['tables'][$view]), $view);
        }
    }
}
