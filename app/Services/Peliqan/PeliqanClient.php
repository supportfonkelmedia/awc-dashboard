<?php

namespace App\Services\Peliqan;

use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class PeliqanClient
{
    public function __construct(
        protected ?string $token = null,
        protected int $timeout = 60,
    ) {
        $this->token = $token ?? (string) config('peliqan.token', '');
        $this->timeout = (int) config('peliqan.timeout', 60);
    }

    /**
     * AWC dashboard handler (?bundle=wms|hubspot|finance|all).
     *
     * @param  array<string, string|int|null>  $query
     * @return array<string, mixed>
     */
    public function fetchAwc(array $query = []): array
    {
        $url = (string) config('peliqan.awc_data_url', '');

        return $this->getJson($url, $query);
    }

    /**
     * Fast 7T WMS KPI aggregates from the dedicated direct-SQL 7T endpoint.
     *
     * @param  array<string, string|int|null>  $query
     * @return array<string, mixed>
     */
    public function fetch7tWms(array $query = []): array
    {
        $url = (string) config('peliqan.awc_7t_url', '');
        $timeout = (int) config('peliqan.wms_timeout', config('peliqan.timeout', 60));

        return $this->getJson($url, $query, $timeout);
    }

    /**
     * MT dashboard handler (?bundle=cashweb|hubspot|sprinter|all + filters).
     *
     * @param  array<string, string|int|null>  $query
     * @return array<string, mixed>
     */
    public function fetchMt(array $query = []): array
    {
        $url = (string) config('peliqan.mt_data_url', '');

        return $this->getJson($url, $query);
    }

    /**
     * 7T schema export handler (?bundle=summary|kpi|full|table + filters).
     *
     * @param  array<string, string|int|null>  $query
     * @return array<string, mixed>
     */
    public function fetch7tSchema(array $query = []): array
    {
        $url = (string) config('peliqan.schema_7t_url', '');

        return $this->getJson($url, $query);
    }

    /**
     * Raw GET to any Peliqan published URL (full URL in config or passed in).
     *
     * @param  array<string, string|int|null>  $query
     * @return array<string, mixed>
     */
    public function fetch(string $absoluteUrl, array $query = []): array
    {
        return $this->getJson($absoluteUrl, $query);
    }

    /**
     * @param  array<string, string|int|null>  $query
     * @return array<string, mixed>
     */
    protected function getJson(string $url, array $query, ?int $timeoutSeconds = null): array
    {
        $url = $this->normalizeUrl($url);
        if ($url === '') {
            throw new PeliqanException('Peliqan URL is not configured (check PELIQAN_*_URL in .env).');
        }

        if ($this->token === '') {
            throw new PeliqanException('Peliqan JWT is not configured (PELIQAN_JWT).');
        }

        $query = $this->filterQuery($query);
        $timeout = $timeoutSeconds ?? $this->timeout;

        $response = Http::timeout($timeout)
            ->acceptJson()
            ->withHeaders([
                'Authorization' => 'JWT '.$this->token,
            ])
            ->get($url, $query);

        return $this->decodeSuccessfulResponse($response, $url);
    }

    protected function normalizeUrl(string $url): string
    {
        $url = trim($url);

        // Common .env typo: PELIQAN_*_URL==https://… leaves a leading "=" in the value.
        while (str_starts_with($url, '=')) {
            $url = ltrim($url, '=');
        }

        return trim($url);
    }

    /**
     * @param  array<string, string|int|null>  $query
     * @return array<string, string>
     */
    protected function filterQuery(array $query): array
    {
        $out = [];
        foreach ($query as $key => $value) {
            if ($value === null || $value === '') {
                continue;
            }
            if (! is_scalar($value)) {
                continue;
            }
            $out[(string) $key] = (string) $value;
        }

        return $out;
    }

    /**
     * @return array<string, mixed>
     */
    protected function decodeSuccessfulResponse(Response $response, string $url): array
    {
        if (! $response->successful()) {
            $body = mb_substr($response->body(), 0, 2000);

            Log::warning('Peliqan HTTP error', [
                'url' => $url,
                'status' => $response->status(),
                'body' => $body,
            ]);

            $detail = '';
            /** @var array<string, mixed>|null $errJson */
            $errJson = $response->json();
            if (is_array($errJson)) {
                $msg = $errJson['message'] ?? $errJson['error'] ?? null;
                if (is_string($msg) && $msg !== '') {
                    $detail = ': '.$msg;
                }
            } elseif ($body !== '') {
                $detail = ': '.mb_substr(trim($body), 0, 300);
            }

            throw new PeliqanException(
                'Peliqan request failed: HTTP '.$response->status().$detail,
                0,
                null,
                is_array($errJson ?? null) ? $errJson : null,
                $response->status(),
            );
        }

        /** @var array<string, mixed>|null $json */
        $json = $response->json();

        if (! is_array($json)) {
            throw new PeliqanException('Peliqan returned a non-JSON response.', 0, null, null, $response->status());
        }

        if (isset($json['status']) && $json['status'] === 'error') {
            $message = is_string($json['message'] ?? null)
                ? $json['message']
                : 'Peliqan script error';

            Log::warning('Peliqan script error', [
                'url' => $url,
                'message' => mb_substr($message, 0, 2000),
            ]);

            throw new PeliqanException($message, 0, null, $json, $response->status());
        }

        return $json;
    }
}
