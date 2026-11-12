<?php

namespace App\Services\Kpi;

use App\Http\Controllers\KpiDashboardController;

/**
 * Static KPI screen payloads for local development / UI review (Overdracht acceptatie baseline).
 */
class KpiScreenFixtureProvider
{
    /**
     * @param  array<string, scalar|null>  $query
     * @return array<string, mixed>|null
     */
    public function bundle(array $query): ?array
    {
        $bundle = strtolower((string) ($query['bundle'] ?? 'screen'));

        return match ($bundle) {
            'screen' => $this->screen(strtolower((string) ($query['scherm'] ?? ''))),
            'controles' => $this->controlesBundle(),
            'registry' => [
                'bundle' => 'registry',
                'kpi_registry' => $this->registryRows(),
                'meta' => $this->meta('registry'),
            ],
            'drill' => $this->drill((string) ($query['views'] ?? '')),
            default => null,
        };
    }

    /**
     * @return array<string, mixed>|null
     */
    public function screen(string $scherm): ?array
    {
        if (! in_array($scherm, KpiDashboardController::SCREENS, true)) {
            return null;
        }

        $config = $this->tegelConfig($scherm);
        $oordeel = $this->oordeelForScherm($scherm);
        $trends = $this->trendsForScherm($scherm);
        $controles = $this->controlesRows();

        $out = [
            'bundle' => 'screen',
            'scherm' => $scherm,
            'tegel_config' => $config,
            'kpi_oordeel' => $oordeel,
            'kpi_registry' => $this->registryRows(),
            'kpi_trend' => $trends,
            'kpi_controles' => $controles,
            'controles_summary' => $this->controlesSummary($controles),
            'errors' => [],
            'meta' => $this->meta('screen'),
        ];

        if ($this->schermUsesOmzetbrug($config)) {
            $out['kpi_omzetbrug'] = $this->omzetbrugRows();
        }

        return $out;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function tegelConfig(string $scherm): array
    {
        $header = [
            [
                'scherm' => 'header',
                'positie' => 1,
                'element' => 'header',
                'titel' => 'Datacontroles',
                'waarde_bron' => 'kpi_controles',
            ],
        ];

        $byScherm = [
            'strategisch' => [
                // Order matches mockup 01: strategische tegels first, then AANVULLEND (Omzetbrug + A/B Players).
                $this->cfgTegel('Bruto marge per loonkosten', 'bruto_marge_per_loonkosten', 'concern', 'FINANCIËLE GEZONDHEID', 'kpi_bm_maand', 'bruto_marge_per_loonkosten', 'concern', 'Cashweb'),
                $this->cfgTegel('% Triple LOB', 'triple_lob', 'concern', 'WAARDE', 'kpi_triple_lob_maand,kpi_triple_lob_te_controleren', 'triple_lob', 'concern', 'Cashweb'),
                $this->cfgTegel('Winrate Verkooppijplijn', 'winrate', 'Verkooppijplijn', 'COMMERCIEEL', 'kpi_winrate_maand,kpi_winrate_fases', 'winrate', 'Verkooppijplijn', 'HubSpot'),
                $this->cfgTegel('Churn', 'churn', 'concern', 'RETENTIE', 'kpi_churn_kwartaal', 'churn', 'concern', 'Cashweb'),
                $this->cfgTegel('OTIF', 'otif', '', 'OPERATIE', null, null, null, '—'),
                $this->cfgTegel('EBITDA', 'ebitda', 'concern', 'FINANCIËLE GEZONDHEID', 'kpi_ebitda_maand,kpi_kosten_maand,kpi_handmatig', 'ebitda', 'concern', 'Cashweb + handmatig'),
                $this->cfgBanner('Omzetbrug', 'omzet_brug', 'concern', 'WAARDE', 'kpi_omzetbrug,kpi_omzetbrug_top,kpi_omzetbrug_klant', 'omzet_brug', 'concern', 'Cashweb'),
                $this->cfgTegel('A/B Players', 'ab_players', '', 'MENSEN', 'kpi_handmatig', null, null, 'Handmatig'),
            ],
            'operationeel' => [
                $this->cfgVast('ICP-interacties', 'in_opbouw', 'Definitie en bron in opbouw.'),
                $this->cfgVast('Client requests per LOB', 'in_opbouw', 'Definitie en bron in opbouw.'),
                $this->cfgTegel('Winrate Verkooppijplijn', 'winrate', 'Verkooppijplijn', '', 'kpi_winrate_maand', 'winrate', 'Verkooppijplijn', 'HubSpot'),
                $this->cfgTegel('Time to onboarding', 'time_to_onboarding', 'alaw', '', 'kpi_onboarding_kwartaal', 'time_to_onboarding', 'alaw', 'HubSpot'),
                $this->cfgTegel('Dock-to-stock binnen 24 uur', 'dock_to_stock', 'alaw', '', 'kpi_d2s_maand', 'dock_to_stock', 'alaw', '7T'),
                $this->cfgVast('Bezettingsgraad', 'in_validatie', 'Definitie wordt gevalideerd.'),
                $this->cfgVast('On-time delivery', 'in_opbouw', 'Definitie en bron in opbouw.'),
                $this->cfgTegel('Churn', 'churn', 'concern', '', 'kpi_churn_kwartaal', 'churn', 'concern', 'Cashweb'),
                $this->cfgTegel('Dossiers per soort', 'acc_dossiers', 'acco', '', 'kpi_acc_dossiers_maand', 'acc_dossiers', 'acco', 'HubSpot'),
            ],
            'tactisch' => [
                $this->cfgTegel('eNPS', 'enps', '', 'sectie', 'kpi_handmatig', null, null, 'Handmatig'),
                $this->cfgSectie('Handmatige invoer', 'kpi_registry', 'Overzicht KPI’s met handmatige invoer.'),
                $this->cfgSectie('Datakwaliteit', 'kpi_controles', 'Controles uit Peliqan.'),
                $this->cfgSectie('Gepland voor 2027', 'kpi_oordeel', 'KPI’s met weergave gepland_2027.'),
            ],
            'awc' => [
                $this->cfgTegel('Bruto marge per loonkosten, AWC', 'bruto_marge_per_loonkosten', 'alaw', '', 'kpi_bm_maand', 'bruto_marge_per_loonkosten', 'alaw', 'Cashweb'),
                $this->cfgTegel('EBITDA, AWC', 'ebitda', 'alaw', '', 'kpi_kosten_maand', 'ebitda', 'alaw', 'Cashweb'),
                $this->cfgBanner('Omzet en klanten, AWC', 'omzet_brug', 'alaw', '', 'kpi_omzetbrug,kpi_omzetbrug_klant', 'omzet_brug', 'alaw', 'Cashweb'),
                $this->cfgTegel('Dock-to-stock binnen 24 uur', 'dock_to_stock', 'alaw', '', 'kpi_d2s_maand', 'dock_to_stock', 'alaw', '7T'),
                $this->cfgVast('Inventory accuracy', 'in_validatie', 'Definitie wordt gevalideerd.'),
                $this->cfgTegel('Throughput', 'throughput', 'alaw', '', 'kpi_awc_ops_maand', 'throughput', 'alaw', '7T'),
                $this->cfgTegel('Damage rate', 'damage_rate', 'alaw', '', 'kpi_awc_ops_maand,kpi_awc_schade_klant', 'damage_rate', 'alaw', '7T'),
                $this->cfgVast('Perfect order rate', 'in_opbouw', 'Definitie en bron in opbouw.'),
                $this->cfgVast('Storage lead time', 'niet_meetbaar', 'Niet betrouwbaar meetbaar in huidige bron.'),
            ],
            'afc' => [
                $this->cfgTegel('Bruto marge per loonkosten, AFC', 'bruto_marge_per_loonkosten', 'pgl1', '', 'kpi_bm_maand', 'bruto_marge_per_loonkosten', 'pgl1', 'Cashweb'),
                $this->cfgTegel('EBITDA, AFC', 'ebitda', 'pgl1', '', 'kpi_kosten_maand', 'ebitda', 'pgl1', 'Cashweb'),
                $this->cfgBanner('Omzet en klanten, AFC', 'omzet_brug', 'pgl1', '', 'kpi_omzetbrug,kpi_omzetbrug_klant', 'omzet_brug', 'pgl1', 'Cashweb'),
                $this->cfgTegel('Winrate AFC Verkooplijn', 'winrate', 'AFC Verkooplijn', '', 'kpi_winrate_maand', 'winrate', 'AFC Verkooplijn', 'HubSpot'),
                $this->cfgTegel('Zendingen', 'afc_zendingen', 'pgl1', 'Volume', 'kpi_afc_sprinter_maand', 'afc_zendingen', 'pgl1', 'Sprinter3000 · zendingen'),
                $this->cfgTegel('Modal split', 'afc_modal_split', 'pgl1', 'Volume', 'kpi_afc_sprinter_maand', 'afc_modal_split', 'pgl1', 'Sprinter3000 · zendingen'),
                $this->cfgTegel('Marge per zending', 'afc_marge_per_zending', 'pgl1', 'Marge', 'kpi_afc_sprinter_maand', 'afc_marge_per_zending', 'pgl1', 'Sprinter3000 · zendingen'),
                $this->cfgVast('Quote conversion', 'in_opbouw', 'Definitie en bron in opbouw.'),
                $this->cfgVast('First time right', 'in_opbouw', 'Definitie en bron in opbouw.'),
            ],
            'acc' => [
                $this->cfgTegel('Bruto marge per loonkosten, ACC', 'bruto_marge_per_loonkosten', 'acco', '', 'kpi_bm_maand', 'bruto_marge_per_loonkosten', 'acco', 'Cashweb'),
                $this->cfgTegel('EBITDA, ACC', 'ebitda', 'acco', '', 'kpi_kosten_maand', 'ebitda', 'acco', 'Cashweb'),
                $this->cfgBanner('Omzet en klanten, ACC', 'omzet_brug', 'acco', '', 'kpi_omzetbrug,kpi_omzetbrug_klant', 'omzet_brug', 'acco', 'Cashweb'),
                $this->cfgTegel('Doorlooptijd dossier', 'acc_doorlooptijd', 'acco', '', 'kpi_acc_doorlooptijd_maand', 'acc_doorlooptijd', 'acco', 'HubSpot'),
                $this->cfgVast('First time right', 'in_opbouw', 'Definitie en bron in opbouw.'),
                $this->cfgVast('On-time delivery', 'in_opbouw', 'Definitie en bron in opbouw.'),
            ],
        ];

        $rows = $byScherm[$scherm] ?? [];
        foreach ($rows as $i => &$row) {
            $row['scherm'] = $scherm;
            if (! isset($row['positie'])) {
                $row['positie'] = $i + 1;
            }
        }
        unset($row);

        return array_merge($header, $rows);
    }

    /**
     * @return array<string, mixed>
     */
    private function cfgTegel(
        string $titel,
        string $kpiCode,
        string $scope,
        string $pijler,
        ?string $drill,
        ?string $trendKpi,
        ?string $trendScope,
        string $bronLabel,
    ): array {
        return [
            'element' => 'tegel',
            'titel' => $titel,
            'kpi_code' => $kpiCode,
            'scope_code' => $scope,
            'pijler' => $pijler,
            'waarde_bron' => 'kpi_oordeel',
            'drill_views' => $drill,
            'trend_kpi_code' => $trendKpi,
            'trend_scope_code' => $trendScope ?? $scope,
            'bron_label' => $bronLabel,
        ];
    }

    /**
     * @return array<string, mixed>
     */
    private function cfgBanner(
        string $titel,
        string $kpiCode,
        string $scope,
        string $pijler,
        string $drill,
        ?string $trendKpi,
        ?string $trendScope,
        string $bronLabel,
    ): array {
        return [
            'element' => 'banner',
            'positie' => 0,
            'titel' => $titel,
            'kpi_code' => $kpiCode,
            'scope_code' => $scope,
            'pijler' => $pijler,
            'waarde_bron' => 'kpi_oordeel',
            'drill_views' => $drill,
            'trend_kpi_code' => $trendKpi,
            'trend_scope_code' => $trendScope ?? $scope,
            'bron_label' => $bronLabel,
        ];
    }

    /**
     * @return array<string, mixed>
     */
    private function cfgVast(string $titel, string $staat, string $tekst): array
    {
        return [
            'element' => 'tegel',
            'titel' => $titel,
            'waarde_bron' => 'vast',
            'vaste_staat' => $staat,
            'vaste_tekst' => $tekst,
            'bron_label' => '—',
        ];
    }

    /**
     * @return array<string, mixed>
     */
    private function cfgSectie(string $titel, string $bron, string $tekst): array
    {
        return [
            'element' => 'sectie',
            'titel' => $titel,
            'pijler' => 'sectie',
            'waarde_bron' => $bron,
            'vaste_tekst' => $tekst,
        ];
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function oordeelForScherm(string $scherm): array
    {
        $all = $this->allOordeelRows();
        $codesByScherm = [
            'strategisch' => ['bruto_marge_per_loonkosten', 'triple_lob', 'winrate', 'churn', 'otif', 'ebitda', 'omzet_brug', 'ab_players'],
            'operationeel' => ['winrate', 'time_to_onboarding', 'dock_to_stock', 'churn', 'acc_dossiers'],
            'tactisch' => ['enps', 'nps_2027', 'automatisering_2027'],
            'awc' => ['bruto_marge_per_loonkosten', 'ebitda', 'omzet_brug', 'dock_to_stock', 'throughput', 'damage_rate'],
            'afc' => ['bruto_marge_per_loonkosten', 'ebitda', 'omzet_brug', 'winrate', 'afc_zendingen', 'afc_modal_split', 'afc_marge_per_zending'],
            'acc' => ['bruto_marge_per_loonkosten', 'ebitda', 'omzet_brug', 'acc_doorlooptijd'],
        ];
        $want = $codesByScherm[$scherm] ?? [];
        $gepland = in_array($scherm, ['tactisch'], true);

        $rows = array_values(array_filter(
            $all,
            fn ($r) => in_array($r['kpi_code'], $want, true)
                || ($gepland && ($r['weergave'] ?? '') === 'gepland_2027'),
        ));

        return $rows;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function allOordeelRows(): array
    {
        $jul = '2026-07-01';
        $sep = '2026-09-22';
        $aug = '2026-08-01';

        return [
            $this->meet('omzet_brug', 'concern', 19_040_567, 17_271_356, 1_769_211, 'euro', 'hoger_beter', $jul),
            $this->meet('omzet_brug', 'alaw', 12_044_618, 10_094_635, 1_949_983, 'euro', 'hoger_beter', $jul),
            $this->meet('omzet_brug', 'pgl1', 6_781_148, 7_018_690, -237_542, 'euro', 'hoger_beter', $jul),
            $this->meet('omzet_brug', 'acco', 214_800, 158_031, 56_769, 'euro', 'hoger_beter', $jul),
            $this->meet('bruto_marge_per_loonkosten', 'concern', 2.4, 2.36, 0.04, 'ratio', 'hoger_beter', $jul),
            $this->meet('bruto_marge_per_loonkosten', 'alaw', 2.21, 2.28, -0.07, 'ratio', 'hoger_beter', $aug),
            $this->meet('bruto_marge_per_loonkosten', 'pgl1', 3.92, 4.09, -0.17, 'ratio', 'hoger_beter', $jul),
            $this->meet('bruto_marge_per_loonkosten', 'acco', 2.51, 2.27, 0.24, 'ratio', 'hoger_beter', $jul),
            $this->meet('triple_lob', 'concern', 8.2, 8.4, -0.2, 'procent', 'hoger_beter', $jul),
            $this->meet('winrate', 'Verkooppijplijn', 42.1, 38.7, 3.4, 'procent', 'hoger_beter', $sep),
            $this->meet('winrate', 'AFC Verkooplijn', null, null, null, 'procent', 'hoger_beter', $sep, 'te_weinig_data', 'Te weinig deals in deze pijplijn.'),
            $this->meet('churn', 'concern', 64, 47, 17, 'aantal', 'lager_beter', $sep),
            $this->meet('ebitda', 'concern', 1_194_998, 1_755_466, -560_468, 'euro', 'hoger_beter', $jul),
            $this->meet('ebitda', 'alaw', 499_121, 892_583, -393_462, 'euro', 'hoger_beter', $jul),
            $this->meet('ebitda', 'pgl1', 576_602, 755_740, -179_138, 'euro', 'hoger_beter', $jul),
            $this->meet('ebitda', 'acco', 119_275, 107_143, 12_132, 'euro', 'hoger_beter', $jul),
            $this->status('otif', '', 'in_opbouw', 'Definitie en data in opbouw.'),
            $this->status('enps', '', 'wacht_op_invoer', 'Nog geen eNPS ingevoerd voor dit kwartaal.'),
            $this->status('ab_players', '', 'wacht_op_invoer', 'Nog geen A/B Players ingevoerd voor dit kwartaal.', 'Daphne'),
            $this->meet('time_to_onboarding', 'alaw', 66.7, null, null, 'dagen', 'lager_beter', $sep),
            $this->meet('dock_to_stock', 'alaw', 88.4, 77.4, 11.0, 'procent', 'hoger_beter', $aug),
            $this->meet('acc_dossiers', 'acco', 7345, null, null, 'aantal', 'neutraal', $sep),
            $this->meet('throughput', 'alaw', 13_588, 16_384, -2_796, 'aantal', 'hoger_beter', $aug),
            $this->meet('damage_rate', 'alaw', 4.6, 1.5, 3.1, 'procent', 'lager_beter', $aug),
            $this->meet('acc_doorlooptijd', 'acco', 2.8, null, null, 'dagen', 'lager_beter', $sep),
            $this->meet('afc_zendingen', 'pgl1', 1117, 1219, -102, 'aantal', 'neutraal', '2026-10-01'),
            $this->meet('afc_modal_split', 'pgl1', 88.7, 91.1, -2.4, 'procent', 'neutraal', '2026-10-01'),
            $this->meet('afc_marge_per_zending', 'pgl1', 152.87, 168.53, -15.66, 'euro', 'hoger_beter', '2026-10-01'),
            [
                'kpi_code' => 'nps_2027',
                'scope_code' => '',
                'naam' => 'NPS',
                'weergave' => 'gepland_2027',
                'leeg_reden' => 'Gepland na implementatie enquête 2027.',
                'tonen_op_dashboard' => true,
            ],
            [
                'kpi_code' => 'automatisering_2027',
                'scope_code' => '',
                'naam' => 'Automatiseringsdoelen',
                'weergave' => 'gepland_2027',
                'leeg_reden' => 'Doelen worden Q4 2026 vastgelegd.',
                'tonen_op_dashboard' => true,
            ],
        ];
    }

    /**
     * @return array<string, mixed>
     */
    private function meet(
        string $kpi,
        string $scope,
        ?float $waarde,
        ?float $vorige,
        ?float $delta,
        string $eenheid,
        string $richting,
        string $standPer,
        ?string $weergave = null,
        ?string $leegReden = null,
    ): array {
        if ($weergave !== null) {
            return [
                'kpi_code' => $kpi,
                'scope_code' => $scope,
                'eenheid' => $eenheid,
                'richting' => $richting,
                'weergave' => $weergave,
                'leeg_reden' => $leegReden,
                'tonen_op_dashboard' => true,
                'bron_bijgewerkt' => $standPer.'T12:00:00Z',
            ];
        }

        return [
            'kpi_code' => $kpi,
            'scope_code' => $scope,
            'eenheid' => $eenheid,
            'richting' => $richting,
            'weergave' => 'meetwaarde',
            'waarde' => $waarde,
            'waarde_vorige' => $vorige,
            'delta' => $delta,
            'stand_per' => $standPer,
            'eigenaar' => 'MT',
            'bron' => 'Fixture',
            'bron_bijgewerkt' => $standPer.'T08:00:00Z',
            'tonen_op_dashboard' => true,
        ];
    }

    /**
     * @return array<string, mixed>
     */
    private function status(
        string $kpi,
        string $scope,
        string $weergave,
        string $leegReden,
        ?string $eigenaar = null,
    ): array {
        return array_filter([
            'kpi_code' => $kpi,
            'scope_code' => $scope,
            'weergave' => $weergave,
            'leeg_reden' => $leegReden,
            'eigenaar' => $eigenaar,
            'tonen_op_dashboard' => true,
            'bron_bijgewerkt' => '2026-09-22T08:00:00Z',
        ], fn ($v) => $v !== null);
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function trendsForScherm(string $scherm): array
    {
        $trends = [];

        if ($scherm === 'strategisch') {
            $trends[] = $this->trend('ebitda', 'concern', '2026-07-01', 1_194_998, 'definitief', 1);
            $trends[] = $this->trend('ebitda', 'concern', '2026-08-01', 1_050_000, 'voorlopig', 2);
            $trends[] = $this->trend('bruto_marge_per_loonkosten', 'concern', '2026-07-01', 2.4, 'definitief', 1);
        }

        if (in_array($scherm, ['operationeel', 'awc'], true)) {
            $trends[] = $this->trend('dock_to_stock', 'alaw', '2026-09-01', 86.9, 'voorlopig', 3);
        }
        if ($scherm === 'afc') {
            $trends[] = $this->trend('afc_zendingen', 'pgl1', '2026-08-01', 1015, 'definitief', 1);
            $trends[] = $this->trend('afc_zendingen', 'pgl1', '2026-09-01', 1219, 'definitief', 2);
            $trends[] = $this->trend('afc_zendingen', 'pgl1', '2026-10-01', 1117, 'definitief', 3);
            $trends[] = $this->trend('afc_zendingen', 'pgl1', '2026-11-01', 363, 'voorlopig', 4);
        }
        if (in_array($scherm, ['operationeel', 'acc'], true)) {
            $trends[] = $this->trend('acc_dossiers', 'acco', '2026-09-01', 224, 'voorlopig', 1, 'Export');
            $trends[] = $this->trend('acc_dossiers', 'acco', '2026-09-01', 177, 'voorlopig', 1, 'Overig');
            $trends[] = $this->trend('acc_dossiers', 'acco', '2026-09-01', 160, 'voorlopig', 1, 'Import');
            $trends[] = $this->trend('acc_dossiers', 'acco', '2026-09-01', 16, 'voorlopig', 1, 'Consult');
        }

        return $trends;
    }

    /**
     * @return array<string, mixed>
     */
    private function trend(
        string $kpi,
        string $scope,
        string $periode,
        float $waarde,
        string $status,
        int $volg,
        string $serie = '',
    ): array {
        return [
            'kpi_code' => $kpi,
            'scope_code' => $scope,
            'serie' => $serie,
            'periode' => $periode,
            'waarde' => $waarde,
            'status' => $status,
            'volgnummer' => $volg,
        ];
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function controlesRows(): array
    {
        return [
            ['status' => 'fout', 'controle' => 'Triple LOB reconciliatie', 'waarde' => 'Afwijking', 'norm' => '0', 'toelichting' => 'Steekproef klantlijst.'],
            ['status' => 'ok', 'controle' => 'Volume Sprinter3000', 'bron' => 'Sprinter3000', 'waarde' => '1117', 'norm' => 'Minimaal 50% van gemiddelde', 'toelichting' => 'Eigen Sprinter-sync, dagelijks.'],
            ['status' => 'let_op', 'controle' => 'HubSpot winrate', 'waarde' => 'Voorlopig', 'norm' => 'Definitief', 'toelichting' => 'Peildatum recent.'],
            ...array_fill(0, 11, ['status' => 'ok', 'controle' => 'Standaard controle', 'waarde' => 'OK', 'norm' => 'OK', 'toelichting' => 'Geen actie.']),
        ];
    }

    /**
     * @param  list<array<string, mixed>>  $rows
     * @return array{fout: int, let_op: int, ok: int}
     */
    private function controlesSummary(array $rows): array
    {
        $summary = ['fout' => 0, 'let_op' => 0, 'ok' => 0];
        foreach ($rows as $row) {
            $status = strtolower((string) ($row['status'] ?? ''));
            if ($status === 'fout') {
                $summary['fout']++;
            } elseif ($status === 'let_op' || $status === 'let op') {
                $summary['let_op']++;
            } elseif ($status === 'ok') {
                $summary['ok']++;
            }
        }

        return $summary;
    }

    /**
     * @return array<string, mixed>
     */
    private function controlesBundle(): array
    {
        $rows = $this->controlesRows();

        return [
            'bundle' => 'controles',
            'kpi_controles' => $rows,
            'controles_summary' => $this->controlesSummary($rows),
            'meta' => $this->meta('controles'),
        ];
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function registryRows(): array
    {
        return [
            ['kpi_code' => 'enps', 'naam' => 'eNPS', 'eigenaar' => 'HR', 'updatefrequentie' => 'Kwartaal', 'bouwstatus' => 'handmatig'],
            ['kpi_code' => 'ab_players', 'naam' => 'A/B Players', 'eigenaar' => 'HR', 'updatefrequentie' => 'Kwartaal', 'bouwstatus' => 'handmatig'],
            ['kpi_code' => 'ebitda', 'naam' => 'EBITDA (concern)', 'eigenaar' => 'Finance', 'updatefrequentie' => 'Kwartaal', 'bouwstatus' => 'handmatig'],
        ];
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function omzetbrugRows(): array
    {
        $components = [
            'Concern' => [
                'start' => 17_271_356,
                'nieuw' => 2_100_000,
                'gegroeid' => 800_000,
                'gekrompen' => -400_000,
                'verloren' => -366_789,
                'eind' => 19_040_567,
            ],
            'AWC' => [
                'start' => 10_094_635,
                'nieuw' => 1_200_000,
                'gegroeid' => 500_000,
                'gekrompen' => -150_000,
                'verloren' => -600_017,
                'eind' => 12_044_618,
            ],
            'AFC' => [
                'start' => 7_018_690,
                'nieuw' => 400_000,
                'gegroeid' => 100_000,
                'gekrompen' => -500_000,
                'verloren' => -237_542,
                'eind' => 6_781_148,
            ],
            'ACC' => [
                'start' => 158_031,
                'nieuw' => 80_000,
                'gegroeid' => 20_000,
                'gekrompen' => -10_000,
                'verloren' => -33_231,
                'eind' => 214_800,
            ],
        ];

        $out = [];
        foreach ($components as $scope => $map) {
            foreach ($map as $component => $bedrag) {
                $out[] = [
                    'scope' => $scope,
                    'component' => $component,
                    'bedrag' => $bedrag,
                    'klanten' => in_array($component, ['start', 'eind'], true) ? null : 12,
                ];
            }
        }

        return $out;
    }

    /**
     * @param  list<array<string, mixed>>  $config
     */
    private function schermUsesOmzetbrug(array $config): bool
    {
        foreach ($config as $row) {
            if (($row['kpi_code'] ?? '') === 'omzet_brug') {
                return true;
            }
        }

        return false;
    }

    /**
     * @return array<string, mixed>
     */
    private function drill(string $viewsRaw): array
    {
        $views = array_values(array_filter(array_map('trim', explode(',', $viewsRaw))));
        $tables = [];
        foreach ($views as $view) {
            $tables[$view] = match ($view) {
                'kpi_controles' => $this->controlesRows(),
                'kpi_registry' => $this->registryRows(),
                'kpi_omzetbrug' => $this->omzetbrugRows(),
                'kpi_handmatig' => [],
                default => [
                    ['periode' => '2026-07-01', 'waarde' => 0, 'status' => 'definitief', 'notitie' => 'Fixture — deploy Peliqan voor echte drill.'],
                ],
            };
        }

        return [
            'bundle' => 'drill',
            'views' => $views,
            'tables' => $tables,
            'errors' => [],
            'meta' => $this->meta('drill'),
        ];
    }

    /**
     * @return array<string, mixed>
     */
    private function meta(string $bundle): array
    {
        return [
            'fixture' => true,
            'fixture_baseline' => '2026-09-22 acceptatietest',
            'bundle' => $bundle,
            'handler_version' => 'fonkel-fixture-v1',
        ];
    }
}
