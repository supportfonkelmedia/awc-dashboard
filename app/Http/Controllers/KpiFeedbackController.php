<?php

namespace App\Http\Controllers;

use App\Models\KpiFeedback;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\Rule;
use Inertia\Inertia;
use Inertia\Response;
use Symfony\Component\HttpFoundation\StreamedResponse;

/**
 * Feedbackknop (MT 10-11-2026): iedereen die is ingelogd kan een fout, verbetering
 * of vraag melden, optioneel met screenshot. Alleen KPI_FEEDBACK_ADMINS zien het
 * overzicht en wijzigen de status. Screenshots staan op de private schijf.
 */
class KpiFeedbackController extends Controller
{
    private const DISK = 'local';

    private const DIR = 'kpi-feedback';

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'type' => ['required', Rule::in(KpiFeedback::TYPES)],
            'bericht' => ['required', 'string', 'max:5000'],
            'scherm' => ['required', Rule::in(KpiDashboardController::SCREENS)],
            'entiteit' => ['nullable', 'string', 'max:32'],
            'kpi_code' => ['nullable', 'string', 'max:64', 'regex:/^[a-z0-9_]+$/'],
            'tegel_titel' => ['nullable', 'string', 'max:255'],
            'url' => ['nullable', 'string', 'max:2048'],
            'screenshot' => ['nullable', 'file', 'mimes:png,jpg,jpeg,webp,gif', 'max:5120'],
        ]);

        $path = $request->hasFile('screenshot')
            ? $request->file('screenshot')->store(self::DIR, self::DISK)
            : null;

        $feedback = KpiFeedback::query()->create([
            ...collect($validated)->except('screenshot')->all(),
            'user_id' => $request->user()->id,
            'screenshot_path' => $path ?: null,
            'status' => 'nieuw',
        ]);

        return response()->json([
            'message' => 'Bedankt, je feedback is ontvangen.',
            'id' => $feedback->id,
        ], 201);
    }

    public function index(Request $request): Response
    {
        $this->authorizeAdmin($request);

        $items = KpiFeedback::query()
            ->with('user:id,name,email')
            ->latest()
            ->limit(500)
            ->get()
            ->map(fn (KpiFeedback $f) => [
                'id' => $f->id,
                'type' => $f->type,
                'bericht' => $f->bericht,
                'scherm' => $f->scherm,
                'entiteit' => $f->entiteit,
                'kpi_code' => $f->kpi_code,
                'tegel_titel' => $f->tegel_titel,
                'url' => $f->url,
                'status' => $f->status,
                'ingediend_door' => $f->user?->name ?? 'Verwijderde gebruiker',
                'ingediend_op' => $f->created_at?->toIso8601String(),
                'screenshot_url' => $f->screenshot_path
                    ? route('kpi.feedback.screenshot', $f)
                    : null,
            ]);

        return Inertia::render('Kpi/Feedback', [
            'items' => $items,
            'statuses' => KpiFeedback::STATUSES,
        ]);
    }

    public function update(Request $request, KpiFeedback $feedback): JsonResponse
    {
        $this->authorizeAdmin($request);

        $validated = $request->validate([
            'status' => ['required', Rule::in(KpiFeedback::STATUSES)],
        ]);

        $feedback->update($validated);

        return response()->json(['status' => $feedback->status]);
    }

    public function screenshot(Request $request, KpiFeedback $feedback): StreamedResponse
    {
        $user = $request->user();
        abort_unless(
            $user->isFeedbackAdmin() || $feedback->user_id === $user->id,
            403,
        );
        abort_unless(
            $feedback->screenshot_path
                && Storage::disk(self::DISK)->exists($feedback->screenshot_path),
            404,
        );

        return Storage::disk(self::DISK)->response($feedback->screenshot_path);
    }

    private function authorizeAdmin(Request $request): void
    {
        abort_unless($request->user()->isFeedbackAdmin(), 403);
    }
}
