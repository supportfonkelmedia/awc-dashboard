<?php

namespace App\Http\Controllers;

use App\Services\Kpi\KpiScreenService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * JSON screen payloads for tooling / acceptatietest (same contract as kpi.peliqan?bundle=screen).
 */
class KpiScreenDataController extends Controller
{
    public function screen(string $scherm, KpiScreenService $kpi): JsonResponse
    {
        if (! in_array($scherm, KpiDashboardController::SCREENS, true)) {
            abort(404);
        }

        $result = $kpi->fetch([
            'bundle' => 'screen',
            'scherm' => $scherm,
        ]);

        return response()->json(
            $result['payload'] ?? ['error' => $result['error']],
            $result['status'],
        );
    }

    public function drill(Request $request, KpiScreenService $kpi): JsonResponse
    {
        $validated = $request->validate([
            'views' => ['required', 'string', 'max:2000'],
            'limit' => ['sometimes', 'integer', 'min:1', 'max:5000'],
        ]);

        $query = [
            'bundle' => 'drill',
            'views' => $validated['views'],
        ];
        if (isset($validated['limit'])) {
            $query['limit'] = $validated['limit'];
        }

        $result = $kpi->fetch($query);

        return response()->json(
            $result['payload'] ?? ['error' => $result['error']],
            $result['status'],
        );
    }

    public function controles(KpiScreenService $kpi): JsonResponse
    {
        $result = $kpi->fetch(['bundle' => 'controles']);

        return response()->json(
            $result['payload'] ?? ['error' => $result['error']],
            $result['status'],
        );
    }
}
