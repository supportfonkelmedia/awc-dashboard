<?php

namespace App\Http\Controllers;

use App\Services\Kpi\KpiScreenService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class KpiPeliqanDataController extends Controller
{
    private const BUNDLES = ['screen', 'controles', 'drill', 'registry'];

    public function __invoke(Request $request, KpiScreenService $kpi): JsonResponse
    {
        $validated = $request->validate([
            'bundle' => ['sometimes', 'string', Rule::in(self::BUNDLES)],
            'scherm' => ['sometimes', 'string', Rule::in(KpiDashboardController::SCREENS)],
            'views' => ['sometimes', 'string', 'max:2000'],
            'limit' => ['sometimes', 'integer', 'min:1', 'max:5000'],
            // Drill-filter op entiteit of pijplijn (scope_code van de tegel), bijv. alaw of "AFC - Verkooplijn".
            'scope' => ['sometimes', 'string', 'max:64', 'regex:/^[A-Za-z0-9 _-]+$/'],
        ]);

        $query = array_filter([
            'bundle' => strtolower((string) ($validated['bundle'] ?? 'screen')),
            'scherm' => $validated['scherm'] ?? null,
            'views' => $validated['views'] ?? null,
            'limit' => $validated['limit'] ?? null,
            'scope' => $validated['scope'] ?? null,
        ], fn ($v) => $v !== null && $v !== '');

        $result = $kpi->fetch($query);

        return response()->json(
            $result['payload'] ?? ['error' => $result['error']],
            $result['status'],
        );
    }
}
