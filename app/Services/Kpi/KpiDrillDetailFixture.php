<?php

namespace App\Services\Kpi;

/**
 * Demo-rijen voor de detail-drills onder Churn en Winrate (één rij per klant / deal),
 * zodat de drawer lokaal zonder Peliqan-token iets laat zien. Namen zijn verzonnen.
 * Kolommen volgen de Peliqan-views kpi_churn_klant_my_queries en kpi_winrate_deal_my_queries
 * (documentation/peliqan-sql/kpi_churn_klant.sql en kpi_winrate_deal.sql).
 */
class KpiDrillDetailFixture
{
    /**
     * @return list<array<string, mixed>>|null
     */
    public function rows(string $view): ?array
    {
        return match ($view) {
            'kpi_churn_klant' => $this->churnKlant(),
            'kpi_winrate_deal' => $this->winrateDeal(),
            'kpi_ebitda_maand' => $this->ebitdaMaand(),
            'kpi_afc_sprinter_maand' => $this->afcSprinterMaand(),
            default => null,
        };
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function churnKlant(): array
    {
        $rijen = [
            ['2026-11-04', 'Demo Trading B.V.', 1, 3, false],
            ['2026-09-18', 'Voorbeeld Brouwerij B.V.', 2, null, false],
            ['2026-09-18', 'Demo Spirits Ltd.', 2, 4, false],
            ['2026-09-03', 'Proef Import GmbH', 25, null, false],
            ['2026-09-03', 'Test Wines S.L.', 25, 2, false],
            ['2026-09-03', 'Demo Logistics B.V.', 25, null, true],
            ['2026-01-15', 'Voorbeeld Foods B.V.', 10, 1, false],
            ['2026-01-15', 'Demo Cosmetics Ltd.', 10, null, false],
            ['2025-12-05', 'Proef Dranken B.V.', 13, null, false],
            ['2025-12-05', 'Test Distillers Ltd.', 13, 5, false],
            ['2024-12-04', 'Oud Demo Handel B.V.', 41, null, true],
        ];

        $out = [];
        foreach ($rijen as $i => [$datum, $klant, $dag, $icp, $weer]) {
            $ts = strtotime($datum);
            $out[] = [
                'scope_code' => 'concern',
                'tegelvenster' => $ts > strtotime('-12 months') ? 'laatste 12 maanden'
                    : ($ts > strtotime('-24 months') ? '12 maanden daarvoor' : 'ouder'),
                'vertrekdatum' => $datum,
                'kwartaal' => 'Q'.(int) ceil(((int) date('n', $ts)) / 3).' '.date('Y', $ts),
                'klant' => $klant,
                'vertrekken_die_dag' => $dag,
                'bulkdag' => $dag >= 10,
                'icp_score' => $icp,
                'nu_weer_klant' => $weer,
                'company_id' => (string) (9_000_000_000 + $i),
            ];
        }

        return $out;
    }

    /**
     * EBITDA per maand per scope, inclusief een maand na vandaag zoals Peliqan die levert bij
     * vooruitgedateerde boekingen (de drawer verbergt die met een melding).
     *
     * @return list<array<string, mixed>>
     */
    private function ebitdaMaand(): array
    {
        $volgende = date('Y-m-01', strtotime('first day of next month'));
        $maanden = [
            [$volgende, 0, -167_763, false],
            [date('Y-m-01'), 349_762, 67_086, false],
            [date('Y-m-01', strtotime('first day of last month')), 1_348_311, 225_410, false],
            [date('Y-m-01', strtotime('first day of -2 months')), 1_339_474, 61_208, true],
        ];
        $out = [];
        foreach (['alaw' => 'AWC', 'pgl1' => 'AFC', 'acco' => 'ACC', 'concern' => 'Concern (AWC, AFC, ACC)'] as $code => $label) {
            foreach ($maanden as [$maand, $omzet, $ebitda, $afgesloten]) {
                $out[] = [
                    'scope_code' => $code,
                    'scope_label' => $label,
                    'maand' => $maand,
                    'omzet' => $omzet,
                    'ebitda' => $ebitda,
                    'ebitda_marge_pct' => $omzet ? round(100 * $ebitda / $omzet, 1) : null,
                    'afgesloten' => $afgesloten,
                ];
            }
        }

        return $out;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function winrateDeal(): array
    {
        $rijen = [
            ['Verkooppijplijn', 'telt mee', 'Demo Wines - opslag', 'Sluiting verloren', 'verloren', '2026-05-12', '2026-11-06', 1, 12000],
            ['Verkooppijplijn', 'telt mee', 'Voorbeeld Spirits - fulfilment', 'Opdracht', 'gewonnen', '2026-03-31', '2026-10-15', 3, 48000],
            ['Verkooppijplijn', 'telt mee', 'Test Liqueurs - douane', 'Opdracht', 'gewonnen', '2026-06-02', '2026-10-15', 3, 9500],
            ['Verkooppijplijn', 'telt mee', 'Proef Foods - opslag', 'Eerste levering', 'gewonnen', '2026-02-18', '2026-09-30', 1, 22000],
            ['Verkooppijplijn', 'telt mee', 'Demo Cosmetics - opslag', 'Sluiting verloren', 'verloren', '2025-12-01', '2026-08-21', 296, null],
            ['Verkooppijplijn', 'telt mee', 'Voorbeeld Handel - transport', 'Sluiting verloren', 'verloren', '2026-01-20', '2026-08-21', 296, 15000],
            ['Verkooppijplijn', 'nog open', 'Test Brouwerij - opslag', 'Offerte verstuurd', null, '2026-10-02', null, null, 31000],
            ['Verkooppijplijn', 'nog open', 'Demo Import - fulfilment', 'Kennismaking', null, '2026-11-03', null, null, null],
            ['AFC - Verkooplijn', 'telt mee', 'Demo Freight - zeevracht', 'Verloren', 'verloren', '2026-04-14', '2026-07-01', 1, null],
            ['AFC - Verkooplijn', 'nog open', 'Voorbeeld Cargo - luchtvracht', 'Offerte', null, '2026-09-09', null, null, null],
        ];

        $out = [];
        foreach ($rijen as $i => [$pijplijn, $venster, $deal, $fase, $uitkomst, $aangemaakt, $beslist, $dag, $bedrag]) {
            $out[] = [
                'scope_code' => $pijplijn,
                'tegelvenster' => $venster,
                'deal' => $deal,
                'fase' => $fase,
                'uitkomst' => $uitkomst,
                'aangemaakt' => $aangemaakt,
                'beslisdatum' => $beslist,
                'beslissingen_die_dag' => $dag,
                'bulkdag' => $dag !== null && $dag >= 10,
                'bedrag' => $bedrag,
                'eigenaar' => $pijplijn === 'Verkooppijplijn' ? 'Demo Verkoper' : null,
                'deal_id' => (string) (8_000_000_000 + $i),
            ];
        }

        return $out;
    }

    /**
     * Zendingen per maand en modaliteit (kolommen als kpi_afc_sprinter_maand), voor de
     * Modal split-tegel. Weg/zee/lucht volgen de orde van grootte van de echte maanden.
     *
     * @return list<array<string, mixed>>
     */
    private function afcSprinterMaand(): array
    {
        $maanden = [
            ['2024-12-01', 733, 713, 15, 5],
            ['2025-01-01', 1287, 1147, 136, 4],
            ['2025-02-01', 878, 817, 57, 4],
            ['2025-03-01', 1017, 936, 72, 9],
            ['2025-04-01', 985, 906, 73, 6],
            ['2025-05-01', 1017, 954, 61, 2],
            ['2025-06-01', 1003, 923, 74, 6],
            ['2025-07-01', 1111, 1015, 96, 0],
            ['2025-08-01', 882, 791, 82, 9],
            ['2025-09-01', 987, 882, 98, 7],
            ['2025-10-01', 968, 888, 73, 7],
            ['2025-11-01', 939, 861, 74, 4],
            ['2025-12-01', 637, 599, 36, 2],
            ['2026-01-01', 1206, 1054, 150, 2],
            ['2026-02-01', 887, 815, 68, 4],
            ['2026-03-01', 1017, 932, 79, 6],
            ['2026-04-01', 1037, 971, 59, 7],
            ['2026-05-01', 1050, 1027, 22, 1],
            ['2026-06-01', 1084, 1044, 37, 3],
            ['2026-07-01', 1367, 1176, 188, 3],
            ['2026-08-01', 1015, 906, 107, 2],
            ['2026-09-01', 1219, 1110, 99, 10],
            ['2026-10-01', 1116, 990, 124, 2],
            ['2026-11-01', 467, 420, 43, 4],
        ];

        return array_map(function (array $m) {
            [$maand, $zendingen, $weg, $zee, $lucht] = $m;
            $pct = fn (int $n) => round(100 * $n / $zendingen, 1);

            return [
                'maand' => $maand,
                'zendingen' => $zendingen,
                'weg' => $weg,
                'zee' => $zee,
                'lucht' => $lucht,
                'overig' => 0,
                'pct_weg' => $pct($weg),
                'pct_zee' => $pct($zee),
                'pct_lucht' => $pct($lucht),
                'status' => $maand >= '2026-11-01' ? 'voorlopig' : 'volledig',
            ];
        }, $maanden);
    }
}
