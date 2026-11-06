<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class KpiInvoerTest extends TestCase
{
    use RefreshDatabase;

    public function test_handmatige_invoer_requires_auth(): void
    {
        $this->postJson('/kpi/invoer/handmatig', [])->assertUnauthorized();
    }

    public function test_handmatige_invoer_stores_enps(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->postJson('/kpi/invoer/handmatig', [
                'kpi_code' => 'enps',
                'scope_code' => 'concern',
                'periode_einde' => '2026-03-31',
                'waarde' => 42,
                'n' => 10,
                'ingevoerd_door' => $user->name,
            ])
            ->assertOk()
            ->assertJsonPath('id', 'enps|concern|2026-03-31');

        $this->assertDatabaseHas('kpi_handmatige_invoer', [
            'id' => 'enps|concern|2026-03-31',
            'waarde' => 42,
        ]);
    }

    public function test_doel_invoer_requires_first_of_month(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->postJson('/kpi/invoer/doelen', [
                'kpi_code' => 'ebitda',
                'scope_code' => 'concern',
                'geldig_vanaf' => '2026-03-15',
                'doel' => 1000000,
                'vastgesteld_door' => $user->name,
            ])
            ->assertStatus(422);
    }

    public function test_ebitda_rejects_sar_year(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->postJson('/kpi/invoer/handmatig', [
                'kpi_code' => 'ebitda',
                'scope_code' => 'concern',
                'periode_einde' => '2025-12-31',
                'waarde' => 500000,
                'n' => 1,
                'ingevoerd_door' => $user->name,
            ])
            ->assertStatus(422);
    }

    public function test_ebitda_stores_quarter(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->postJson('/kpi/invoer/handmatig', [
                'kpi_code' => 'ebitda',
                'scope_code' => 'concern',
                'periode_einde' => '2026-09-30',
                'waarde' => 412500,
                'n' => 1,
                'ingevoerd_door' => $user->name,
            ])
            ->assertOk()
            ->assertJsonPath('id', 'ebitda|concern|2026-09-30');
    }

    public function test_doel_invoer_stores_row(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->postJson('/kpi/invoer/doelen', [
                'kpi_code' => 'ebitda',
                'scope_code' => 'concern',
                'geldig_vanaf' => '2026-04-01',
                'doel' => 1200000,
                'marge_bijna' => 50000,
                'vastgesteld_door' => $user->name,
            ])
            ->assertOk()
            ->assertJsonPath('id', 'ebitda|concern|2026-04-01');
    }
}
