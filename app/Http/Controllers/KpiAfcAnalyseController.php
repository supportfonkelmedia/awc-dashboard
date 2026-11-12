<?php

namespace App\Http\Controllers;

use App\Services\Kpi\AfcAnalyseFixture;
use App\Services\Kpi\KpiScreenService;
use Inertia\Inertia;
use Inertia\Response;

/**
 * AFC-analyse: verdieping onder het AFC-scherm (omzet, marge, klanten, eigenaren, aansluiting met Cash).
 * Data komt via de drill-route uit de kpi_afc_*-views (zie documentation/AFC-analyse.md).
 */
class KpiAfcAnalyseController extends Controller
{
    public function __invoke(KpiScreenService $kpi): Response
    {
        return Inertia::render('Kpi/AfcAnalyse', [
            'peliqanError' => $kpi->usesFixture() ? null : $kpi->configurationError(),
            'kpiUsesFixture' => $kpi->usesFixture(),
            // Peliqan rekent "jaar t/m vandaag" met current_date; de demo-data met een vaste datum.
            'vandaag' => $kpi->usesFixture()
                ? AfcAnalyseFixture::VANDAAG
                : now('Europe/Amsterdam')->toDateString(),
        ]);
    }
}
