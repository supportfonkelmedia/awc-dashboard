<?php

namespace App\Http\Controllers;

use App\Models\KpiDoelInvoer;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\Rule;

class KpiDoelInvoerController extends Controller
{
    /** Scopes uit Overdracht (geen pglh). */
    private const SCOPES = [
        'concern',
        'alaw',
        'pgl1',
        'acco',
        'Verkooppijplijn',
        'AFC - Verkooplijn',
    ];

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'kpi_code' => ['required', 'string', 'max:64', 'regex:/^[a-z0-9_]+$/'],
            'scope_code' => ['required', 'string', Rule::in(self::SCOPES)],
            'geldig_vanaf' => ['required', 'date'],
            'doel' => ['required', 'numeric'],
            'marge_bijna' => ['nullable', 'numeric', 'min:0'],
            'vastgesteld_door' => ['required', 'string', 'max:255'],
            'opmerking' => ['nullable', 'string', 'max:2000'],
        ]);

        $geldig = Carbon::parse($validated['geldig_vanaf']);
        if ((int) $geldig->day !== 1) {
            return response()->json([
                'message' => 'geldig_vanaf moet de 1e van een maand zijn.',
            ], 422);
        }

        $id = implode('|', [
            $validated['kpi_code'],
            $validated['scope_code'],
            $geldig->toDateString(),
        ]);

        DB::transaction(function () use ($validated, $id, $geldig) {
            KpiDoelInvoer::query()->updateOrCreate(
                ['id' => $id],
                [
                    'kpi_code' => $validated['kpi_code'],
                    'scope_code' => $validated['scope_code'],
                    'geldig_vanaf' => $geldig->toDateString(),
                    'doel' => $validated['doel'],
                    'marge_bijna' => $validated['marge_bijna'] ?? null,
                    'vastgesteld_door' => $validated['vastgesteld_door'],
                    'ingevoerd_op' => now(),
                    'opmerking' => $validated['opmerking'] ?? null,
                ],
            );
        });

        return response()->json([
            'message' => 'Doel opgeslagen in Fonkel (MariaDB). Peliqan kpi_invoer.doelen sync volgt via beheer.',
            'id' => $id,
        ]);
    }
}
