<?php

namespace Tests\Feature;

use App\Models\KpiFeedback;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Storage;
use Inertia\Testing\AssertableInertia as Assert;
use Tests\TestCase;

class KpiFeedbackTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('local');
        Config::set('kpi_feedback.admin_emails', ['beheer@example.com']);
    }

    private ?User $admin = null;

    private function admin(): User
    {
        // Hoofdletters: de adminlijst vergelijkt zonder hoofdlettergevoeligheid.
        return $this->admin ??= User::factory()->create(['email' => 'Beheer@Example.com']);
    }

    public function test_store_requires_auth(): void
    {
        $this->postJson('/kpi/feedback', [])->assertUnauthorized();
    }

    public function test_store_saves_feedback_with_context_and_screenshot(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->post('/kpi/feedback', [
            'type' => 'fout',
            'bericht' => 'Marge AWC klopt niet met Cashweb.',
            'scherm' => 'strategisch',
            'entiteit' => 'alaw',
            'kpi_code' => 'bruto_marge_per_loonkosten',
            'tegel_titel' => 'Bruto marge per loonkosten, AWC',
            'url' => '/kpi/strategisch?entiteit=awc',
            'screenshot' => UploadedFile::fake()->image('scherm.png', 800, 600),
        ], ['Accept' => 'application/json']);

        $response->assertCreated();

        $feedback = KpiFeedback::query()->sole();
        $this->assertSame($user->id, $feedback->user_id);
        $this->assertSame('nieuw', $feedback->status);
        $this->assertSame('alaw', $feedback->entiteit);
        $this->assertNotNull($feedback->screenshot_path);
        Storage::disk('local')->assertExists($feedback->screenshot_path);
    }

    public function test_store_rejects_unknown_type_screen_and_non_image(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->post('/kpi/feedback', [
                'type' => 'klacht',
                'bericht' => 'x',
                'scherm' => 'onbekend',
                'screenshot' => UploadedFile::fake()->create('script.svg', 10, 'image/svg+xml'),
            ], ['Accept' => 'application/json'])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['type', 'scherm', 'screenshot']);

        $this->assertDatabaseCount('kpi_feedback', 0);
    }

    public function test_overview_is_admin_only(): void
    {
        $this->actingAs(User::factory()->create())
            ->get('/kpi/feedback')
            ->assertForbidden();

        KpiFeedback::query()->create([
            'type' => 'vraag',
            'bericht' => 'Wat telt mee in churn?',
            'scherm' => 'strategisch',
            'status' => 'nieuw',
        ]);

        $this->actingAs($this->admin())
            ->get('/kpi/feedback')
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('Kpi/Feedback')
                ->has('items', 1)
                ->where('items.0.bericht', 'Wat telt mee in churn?')
                ->where('items.0.screenshot_url', null));
    }

    public function test_admin_flag_is_shared_with_pages(): void
    {
        $this->actingAs($this->admin())
            ->get('/kpi/strategisch')
            ->assertInertia(fn (Assert $page) => $page->where('auth.isFeedbackAdmin', true));

        $this->actingAs(User::factory()->create())
            ->get('/kpi/strategisch')
            ->assertInertia(fn (Assert $page) => $page->where('auth.isFeedbackAdmin', false));
    }

    public function test_only_admin_can_change_status(): void
    {
        $feedback = KpiFeedback::query()->create([
            'type' => 'fout',
            'bericht' => 'x',
            'scherm' => 'afc',
            'status' => 'nieuw',
        ]);

        $this->actingAs(User::factory()->create())
            ->patchJson("/kpi/feedback/{$feedback->id}", ['status' => 'afgerond'])
            ->assertForbidden();

        $this->actingAs($this->admin())
            ->patchJson("/kpi/feedback/{$feedback->id}", ['status' => 'gesloten'])
            ->assertStatus(422);

        $this->actingAs($this->admin())
            ->patchJson("/kpi/feedback/{$feedback->id}", ['status' => 'in_behandeling'])
            ->assertOk();

        $this->assertSame('in_behandeling', $feedback->fresh()->status);
    }

    public function test_screenshot_visible_to_submitter_and_admin_only(): void
    {
        $owner = User::factory()->create();
        $path = UploadedFile::fake()->image('s.png')->store('kpi-feedback', 'local');
        $feedback = KpiFeedback::query()->create([
            'user_id' => $owner->id,
            'type' => 'fout',
            'bericht' => 'x',
            'scherm' => 'acc',
            'screenshot_path' => $path,
            'status' => 'nieuw',
        ]);
        $url = "/kpi/feedback/{$feedback->id}/screenshot";

        $this->actingAs($owner)->get($url)->assertOk();
        $this->actingAs($this->admin())->get($url)->assertOk();
        $this->actingAs(User::factory()->create())->get($url)->assertForbidden();
    }
}
