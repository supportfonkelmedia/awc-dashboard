<?php

namespace App\Services\Peliqan;

use RuntimeException;
use Throwable;

class PeliqanException extends RuntimeException
{
    /**
     * @param  array<string, mixed>|null  $payload
     */
    public function __construct(
        string $message,
        int $code = 0,
        ?Throwable $previous = null,
        public readonly ?array $payload = null,
        public readonly ?int $httpStatus = null,
    ) {
        parent::__construct($message, $code, $previous);
    }
}
