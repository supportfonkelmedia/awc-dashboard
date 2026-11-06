<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class KpiScreenDataTest extends TestCase
{
    use RefreshDatabase;

    public function test_screen_api_requires_auth(): void
    {
        $this->getJson('/kpi/api/screens/strategisch')->assertUnauthorized();
    }

    public function test_screen_api_returns_503_when_peliqan_not_configured(): void
    {
        config([
            'peliqan.token' => '',
            'peliqan.kpi_data_url' => '',
            'kpi.use_fixture' => false,
            'kpi.fallback_fixture' => false,
        ]);

        $user = User::factory()->create();

        $this->actingAs($user)
            ->getJson('/kpi/api/screens/strategisch')
            ->assertStatus(503)
            ->assertJsonPath('error', fn ($m) => str_contains((string) $m, 'PELIQAN'));
    }

    public function test_drill_api_validates_views(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->getJson('/kpi/api/drill')
            ->assertStatus(422);
    }
}
