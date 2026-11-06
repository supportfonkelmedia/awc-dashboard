<?php

namespace App\Http\Controllers;

use App\Services\Kpi\KpiScreenService;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;
use Symfony\Component\HttpFoundation\Response as HttpResponse;

class KpiDashboardController extends Controller
{
    /** @var list<string> */
    public const SCREENS = [
        'strategisch',
        'operationeel',
        'tactisch',
        'awc',
        'afc',
        'acc',
    ];

    public function __invoke(Request $request, string $scherm, KpiScreenService $kpi): Response|HttpResponse
    {
        if (! in_array($scherm, self::SCREENS, true)) {
            abort(404);
        }

        return Inertia::render('Kpi/Screen', [
            'scherm' => $scherm,
            'peliqanError' => $kpi->usesFixture() ? null : $kpi->configurationError(),
            'kpiUsesFixture' => $kpi->usesFixture(),
        ]);
    }
}
