<?php

namespace App\Services\Kpi;

/**
 * Demo-data voor de AFC-analyse (lokaal / zonder Peliqan). Zelfde kolommen als de
 * Peliqan-views in documentation/AFC-analyse.md. Verzonnen klanten en medewerkers;
 * de grootte-orde lijkt op AFC zodat de pagina realistisch oogt.
 */
class AfcAnalyseFixture
{
    /** Vaste "vandaag" zodat de demo-data en tests stabiel zijn. */
    public const VANDAAG = '2026-11-12';

    public const VIEWS = [
        'kpi_afc_zending_maand',
        'kpi_afc_eigenaar_maand',
        'kpi_afc_klant_jaar',
        'kpi_afc_klant',
        'kpi_afc_klant_retentie_jaar',
        'kpi_afc_resultaat_maand',
    ];

    /**
     * Basis per maand: [modaliteit, richting, zendingen, omzet per zending, marge %, invoerrechten % van omzet].
     */
    private const STROMEN = [
        ['Weg', 'Export', 700, 320, 0.29, 0.01],
        ['Weg', 'Import', 150, 620, 0.22, 0.18],
        ['Weg', 'Domestic', 110, 120, 0.36, 0.0],
        ['Zee', 'Import', 48, 4300, 0.09, 0.25],
        ['Zee', 'Export', 20, 1900, 0.14, 0.0],
        ['Zee', 'Domestic', 9, 700, 0.2, 0.0],
        ['Lucht', 'Import', 3, 6000, 0.12, 0.08],
        ['Lucht', 'Export', 6, 850, 0.2, 0.0],
        ['Lucht', 'Domestic', 2, 1000, 0.15, 0.1],
    ];

    private const SEIZOEN = [1 => 1.12, 0.86, 1.0, 0.98, 1.02, 1.04, 1.18, 0.9, 1.08, 1.05, 0.95, 0.66];

    private const JAARFACTOR = [2024 => 1.0, 2025 => 0.93, 2026 => 1.04];

    private const EIGENAREN = [
        ['Medewerker A', 'Road'], ['Medewerker B', 'Road'], ['Medewerker C', 'Road'],
        ['Medewerker D', 'Sea'], ['Medewerker E', 'Sea'], ['Medewerker F', 'Air'],
        ['Medewerker G', '(geen)'], ['Medewerker H', 'Road'], ['Medewerker I', '(geen)'],
    ];

    /**
     * @return list<array<string, mixed>>|null
     */
    public function rows(string $view): ?array
    {
        return match ($view) {
            'kpi_afc_zending_maand' => $this->zendingMaand(),
            'kpi_afc_eigenaar_maand' => $this->eigenaarMaand(),
            'kpi_afc_klant_jaar' => $this->klantJaar(),
            'kpi_afc_klant' => $this->klanten(),
            'kpi_afc_klant_retentie_jaar' => $this->retentie(),
            'kpi_afc_resultaat_maand' => $this->resultaatMaand(),
            default => null,
        };
    }

    /** Deterministische ruis tussen 1 - $spreiding en 1 + $spreiding. */
    private function ruis(string $sleutel, float $spreiding = 0.08): float
    {
        $h = crc32($sleutel) / 4294967295;

        return 1 + ($h * 2 - 1) * $spreiding;
    }

    /**
     * Maanden t/m vandaag; voor de lopende maand en dezelfde maand in eerdere jaren
     * splitsen we in een deel binnen en buiten het ytd-venster.
     *
     * @return list<array{maand: string, jaar: int, mnd: int, ytd: bool, aandeel: float}>
     */
    private function perioden(int $vanafJaar = 2024): array
    {
        [$vj, $vm, $vd] = array_map('intval', explode('-', self::VANDAAG));
        $deelBinnen = $vd / 30;
        $out = [];
        for ($jaar = $vanafJaar; $jaar <= $vj; $jaar++) {
            for ($mnd = 1; $mnd <= 12; $mnd++) {
                if ($jaar === $vj && $mnd > $vm) {
                    break;
                }
                $maand = sprintf('%04d-%02d-01', $jaar, $mnd);
                if ($mnd < $vm) {
                    $out[] = ['maand' => $maand, 'jaar' => $jaar, 'mnd' => $mnd, 'ytd' => true, 'aandeel' => 1.0];
                } elseif ($mnd === $vm) {
                    $out[] = ['maand' => $maand, 'jaar' => $jaar, 'mnd' => $mnd, 'ytd' => true, 'aandeel' => $deelBinnen];
                    if ($jaar < $vj) {
                        $out[] = ['maand' => $maand, 'jaar' => $jaar, 'mnd' => $mnd, 'ytd' => false, 'aandeel' => 1 - $deelBinnen];
                    }
                } else {
                    $out[] = ['maand' => $maand, 'jaar' => $jaar, 'mnd' => $mnd, 'ytd' => false, 'aandeel' => 1.0];
                }
            }
        }

        return $out;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function zendingMaand(): array
    {
        $rows = [];
        foreach ($this->perioden() as $p) {
            $factor = self::SEIZOEN[$p['mnd']] * self::JAARFACTOR[$p['jaar']] * $p['aandeel'];
            foreach (self::STROMEN as [$mod, $richting, $n, $perZending, $margePct, $rechtenPct]) {
                $sleutel = "{$p['maand']}|{$mod}|{$richting}|".($p['ytd'] ? 1 : 0);
                $zendingen = (int) max(0, round($n * $factor * $this->ruis($sleutel.'n')));
                if ($zendingen === 0) {
                    continue;
                }
                $omzet = round($zendingen * $perZending * $this->ruis($sleutel.'o', 0.12), 2);
                $marge = round($omzet * $margePct * $this->ruis($sleutel.'m', 0.15), 2);
                $isLopend = $p['maand'] === substr(self::VANDAAG, 0, 7).'-01';
                $rows[] = [
                    'maand' => $p['maand'],
                    'jaar' => $p['jaar'],
                    'maandnummer' => $p['mnd'],
                    'modaliteit' => $mod,
                    'richting' => $richting,
                    'ytd_venster' => $p['ytd'],
                    'zendingen' => $zendingen,
                    'zendingen_open' => $isLopend ? (int) round($zendingen * 0.8) : 0,
                    'omzet' => $omzet,
                    'omzet_incl_invoerrechten' => round($omzet * (1 + $rechtenPct), 2),
                    'marge' => $marge,
                ];
            }
        }

        return $rows;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function eigenaarMaand(): array
    {
        $gewichten = [0.2, 0.17, 0.14, 0.12, 0.1, 0.07, 0.08, 0.07, 0.05];
        $rows = [];
        foreach ($this->perioden(2025) as $p) {
            $factor = self::SEIZOEN[$p['mnd']] * self::JAARFACTOR[$p['jaar']] * $p['aandeel'];
            foreach (self::EIGENAREN as $i => [$naam, $afdeling]) {
                foreach (['Export' => 0.62, 'Import' => 0.26, 'Domestic' => 0.12] as $richting => $aandeel) {
                    $sleutel = "{$p['maand']}|{$naam}|{$richting}|".($p['ytd'] ? 1 : 0);
                    $zendingen = (int) round(1060 * $factor * $gewichten[$i] * $aandeel * $this->ruis($sleutel));
                    if ($zendingen === 0) {
                        continue;
                    }
                    $omzet = round($zendingen * 560 * $this->ruis($sleutel.'o', 0.2), 2);
                    $rows[] = [
                        'maand' => $p['maand'],
                        'jaar' => $p['jaar'],
                        'eigenaar' => $naam,
                        'afdeling' => $afdeling,
                        'richting' => $richting,
                        'ytd_venster' => $p['ytd'],
                        'zendingen' => $zendingen,
                        'omzet' => $omzet,
                        'marge' => round($omzet * 0.21 * $this->ruis($sleutel.'m', 0.25), 2),
                    ];
                }
            }
        }

        return $rows;
    }

    /**
     * @return list<array{id: string, naam: string, debiteur: ?string, omzet: float, mix: array<string, float>}>
     */
    private function klantgroepen(): array
    {
        $out = [];
        for ($i = 1; $i <= 70; $i++) {
            $omzet = 1_350_000 / pow($i, 1.05);
            $zeeZwaar = $i % 7 === 3;
            $out[] = [
                'id' => $i % 11 === 0 ? 'S'.(40000 + $i) : (string) (100000 + $i * 37),
                'naam' => sprintf('Demoklant %02d B.V.', $i),
                'debiteur' => $i % 11 === 0 ? null : (string) (100000 + $i * 37),
                'omzet' => $omzet,
                'mix' => $zeeZwaar
                    ? ['Zee|Import' => 0.7, 'Weg|Import' => 0.3]
                    : ($i % 5 === 0
                        ? ['Weg|Domestic' => 0.6, 'Weg|Export' => 0.4]
                        : ['Weg|Export' => 0.75, 'Weg|Import' => 0.2, 'Lucht|Export' => 0.05]),
            ];
        }

        return $out;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function klantJaar(): array
    {
        $margePct = ['Weg' => 0.27, 'Zee' => 0.08, 'Lucht' => 0.18];
        $perZending = ['Weg' => 380, 'Zee' => 4200, 'Lucht' => 900];
        $rows = [];
        foreach ($this->klantgroepen() as $g) {
            foreach ([2025, 2026] as $jaar) {
                foreach ([true, false] as $ytd) {
                    if ($jaar === 2026 && ! $ytd) {
                        continue;
                    }
                    $deel = $ytd ? 0.86 : 0.14;
                    foreach ($g['mix'] as $combi => $aandeel) {
                        [$mod, $richting] = explode('|', $combi);
                        $sleutel = "{$g['id']}|{$jaar}|{$combi}|".($ytd ? 1 : 0);
                        $omzet = round($g['omzet'] * $aandeel * $deel * self::JAARFACTOR[$jaar] * $this->ruis($sleutel, 0.3), 2);
                        $zendingen = (int) max(1, round($omzet / $perZending[$mod]));
                        $rows[] = [
                            'klantgroep_id' => $g['id'],
                            'klant' => $g['naam'],
                            'debiteurnummer' => $g['debiteur'],
                            'jaar' => $jaar,
                            'richting' => $richting,
                            'modaliteit' => $mod,
                            'ytd_venster' => $ytd,
                            'zendingen' => $zendingen,
                            'omzet' => $omzet,
                            'marge' => round($omzet * $margePct[$mod] * $this->ruis($sleutel.'m', 0.6), 2),
                        ];
                    }
                }
            }
        }

        return $rows;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function klanten(): array
    {
        $statussen = ['Actief', 'Actief', 'Actief', 'Dalend', 'Nieuw', 'Verloren', 'Eenmalig', 'Actief', 'Verloren', 'Actief'];
        $vandaag = new \DateTimeImmutable(self::VANDAAG);
        $rows = [];
        foreach ($this->klantgroepen() as $i => $g) {
            $status = $statussen[$i % count($statussen)];
            $dagen = match ($status) {
                'Verloren' => 120 + ($i * 13) % 400,
                'Eenmalig' => 100 + ($i * 7) % 300,
                default => ($i * 3) % 40,
            };
            $eerste = match ($status) {
                'Nieuw' => $vandaag->modify('-'.(60 + ($i * 11) % 280).' days'),
                default => new \DateTimeImmutable('2023-0'.(3 + $i % 6).'-1'.($i % 9)),
            };
            $omzet12 = $status === 'Verloren' || $status === 'Eenmalig' ? 0 : round($g['omzet'] * $this->ruis($g['id'], 0.2), 2);
            $omzetVorig = match ($status) {
                'Nieuw' => 0,
                'Dalend' => round($omzet12 * 1.9, 2),
                'Verloren' => round($g['omzet'] * 0.8, 2),
                'Eenmalig' => round(900 + $i * 40, 2),
                default => round($omzet12 * $this->ruis($g['id'].'v', 0.2), 2),
            };
            $mods = implode(', ', array_unique(array_map(
                fn ($c) => ['Weg' => 'Road', 'Zee' => 'Sea', 'Lucht' => 'Air'][explode('|', $c)[0]],
                array_keys($g['mix']),
            )));
            $rows[] = [
                'klant_id' => 35000 + $i,
                'klant' => $g['naam'],
                'klantgroep_id' => $g['id'],
                'debiteurnummer' => $g['debiteur'],
                'klantstatus' => $status,
                'eerste_zending' => $eerste->format('Y-m-d'),
                'laatste_zending' => $vandaag->modify("-{$dagen} days")->format('Y-m-d'),
                'dagen_sinds_laatste_zending' => $dagen,
                'zendingen_totaal' => $status === 'Eenmalig' ? 1 : (int) round($g['omzet'] / 300),
                'zendingen_12m' => $omzet12 > 0 ? (int) round($omzet12 / 450) : 0,
                'omzet_12m' => $omzet12,
                'marge_12m' => round($omzet12 * 0.2, 2),
                'omzet_vorige_12m' => $omzetVorig,
                'marge_vorige_12m' => round($omzetVorig * 0.2, 2),
                'modaliteiten_12m' => $omzet12 > 0 ? $mods : null,
                'eigenaren_12m' => self::EIGENAREN[$i % count(self::EIGENAREN)][0],
                'nieuwe_dienst_dit_jaar' => $i % 9 === 4,
            ];
        }

        return $rows;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function retentie(): array
    {
        $basis = [
            [2023, 330, 0, 0, 330, 0, 104, 0, 0, 4_100_000],
            [2024, 342, 228, 102, 114, 0, 90, 330, 255_000, 470_000],
            [2025, 340, 231, 111, 99, 10, 101, 342, 248_000, 300_000],
            [2026, 338, 233, 107, 84, 21, 99, 340, 262_000, 268_000],
        ];
        $rows = [];
        foreach ($basis as [$jaar, $actief, $behouden, $weg, $nieuw, $terug, $een, $vorig, $omzetWeg, $omzetNieuw]) {
            $rows[] = [
                'jaar' => $jaar,
                'actieve_klanten' => $actief,
                'behouden' => $behouden,
                'weggevallen' => $weg,
                'nieuw' => $nieuw,
                'teruggekeerd' => $terug,
                'met_1_zending' => $een,
                'actief_vorig_jaar' => $vorig,
                'omzet_weggevallen_vorig_jaar' => $omzetWeg,
                'omzet_nieuwe_klanten' => $omzetNieuw,
                'retentie_pct' => $vorig ? round(100 * $behouden / $vorig, 1) : null,
                'churn_pct' => $vorig ? round(100 * $weg / $vorig, 1) : null,
                'lopend_jaar' => $jaar === 2026,
            ];
        }

        return $rows;
    }

    /**
     * @return list<array<string, mixed>>
     */
    private function resultaatMaand(): array
    {
        $rows = [];
        [$vj, $vm] = array_map('intval', explode('-', self::VANDAAG));
        for ($jaar = 2024; $jaar <= $vj; $jaar++) {
            for ($mnd = 1; $mnd <= 12; $mnd++) {
                $sleutel = "{$jaar}-{$mnd}";
                $toekomst = $jaar === $vj && $mnd > $vm;
                $lopend = $jaar === $vj && $mnd === $vm;
                $deel = $toekomst ? 0 : ($lopend ? 0.3 : 1);
                $omzet = round(560_000 * self::SEIZOEN[$mnd] * self::JAARFACTOR[$jaar] * $deel * $this->ruis($sleutel, 0.15), 2);
                $kostprijs = round($omzet * 0.79 * $this->ruis($sleutel.'k', 0.06) + ($toekomst ? 17_000 : 0), 2);
                $bedrijfskosten = round(($toekomst ? 27_000 : 72_000) * $this->ruis($sleutel.'b', 0.12), 2);
                $rechten = round($omzet * 0.06, 2);
                $rows[] = [
                    'periode_id' => $jaar * 100 + $mnd,
                    'boekjaar' => $jaar,
                    'maandnummer' => $mnd,
                    'maand' => sprintf('%04d-%02d-01', $jaar, $mnd),
                    'omzet' => $omzet,
                    'invoerrechten_doorbelast' => $rechten,
                    'omzet_incl_invoerrechten' => round($omzet + $rechten, 2),
                    'btw_verkoop' => round($omzet * 0.05, 2),
                    'kostprijs' => $kostprijs,
                    'kostprijs_sim_cargo' => round($kostprijs * 0.09, 2),
                    'kostprijs_svz' => round($kostprijs * 0.2, 2),
                    'brutomarge' => round($omzet - $kostprijs, 2),
                    'brutomarge_pct' => $omzet ? round(100 * ($omzet - $kostprijs) / $omzet, 1) : null,
                    'bedrijfskosten' => $bedrijfskosten,
                    'resultaat_humber' => 0,
                    'resultaat_voor_belasting' => round($omzet - $kostprijs - $bedrijfskosten, 2),
                    'vennootschapsbelasting' => 0,
                    'resultaat_na_belasting' => round($omzet - $kostprijs - $bedrijfskosten, 2),
                    'periode_afwijkend' => $mnd === 1 && $jaar > 2024 ? 40 : 0,
                ];
            }
        }

        return $rows;
    }
}
