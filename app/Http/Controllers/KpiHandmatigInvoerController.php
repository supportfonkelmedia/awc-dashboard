<?php

namespace App\Http\Controllers;

use App\Models\KpiHandmatigeInvoer;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\Rule;

class KpiHandmatigInvoerController extends Controller
{
    /** KPI's met bouwstatus handmatig in Overdracht (geen EBITDA SAR-rijen via dit formulier). */
    private const HANDMATIG_KPI_CODES = ['enps', 'ab_players', 'ebitda'];

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'kpi_code' => ['required', 'string', Rule::in(self::HANDMATIG_KPI_CODES)],
            'scope_code' => ['required', 'string', Rule::in(['concern'])],
            'periode_einde' => ['required', 'date'],
            'waarde' => ['required', 'numeric'],
            'n' => ['required', 'integer', 'min:1'],
            'ingevoerd_door' => ['required', 'string', 'max:255'],
            'opmerking' => ['nullable', 'string', 'max:2000'],
        ]);

        if ($validated['kpi_code'] === 'enps') {
            if ($validated['waarde'] < -100 || $validated['waarde'] > 100) {
                return response()->json([
                    'message' => 'eNPS moet tussen −100 en 100 liggen.',
                ], 422);
            }
        }

        if ($validated['kpi_code'] === 'ab_players') {
            if ($validated['waarde'] < 0 || $validated['waarde'] > 100) {
                return response()->json([
                    'message' => 'A/B Players moet tussen 0 en 100 procent liggen.',
                ], 422);
            }
        }

        if ($validated['kpi_code'] === 'ebitda') {
            $pe = Carbon::parse($validated['periode_einde']);
            $allowedEnds = ['03-31', '06-30', '09-30', '12-31'];
            $md = $pe->format('m-d');
            if (! in_array($md, $allowedEnds, true)) {
                return response()->json([
                    'message' => 'EBITDA periode_einde moet het laatste dag van een kwartaal zijn.',
                ], 422);
            }
            if ((int) $pe->year <= 2025) {
                return response()->json([
                    'message' => 'Historische SAR-jaarcijfers (2019–2025) niet via dit formulier.',
                ], 422);
            }
            $validated['n'] = 1;
        }

        $id = implode('|', [
            $validated['kpi_code'],
            $validated['scope_code'],
            $validated['periode_einde'],
        ]);

        DB::transaction(function () use ($validated, $id) {
            KpiHandmatigeInvoer::query()->updateOrCreate(
                ['id' => $id],
                [
                    'kpi_code' => $validated['kpi_code'],
                    'scope_code' => $validated['scope_code'],
                    'periode_einde' => $validated['periode_einde'],
                    'waarde' => $validated['waarde'],
                    'n' => $validated['n'],
                    'ingevoerd_door' => $validated['ingevoerd_door'],
                    'ingevoerd_op' => now(),
                    'opmerking' => $validated['opmerking'] ?? null,
                ],
            );
        });

        return response()->json([
            'message' => 'Invoer opgeslagen in Fonkel (MariaDB). Peliqan kpi_invoer.sync volgt via beheer.',
            'id' => $id,
        ]);
    }
}
