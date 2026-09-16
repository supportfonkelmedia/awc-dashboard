<?php

namespace App\Support;

final class RegistrationAllowlist
{
    public static function isEnabled(): bool
    {
        return (bool) config('registration.allowlist_enabled', true);
    }

    /**
     * @return list<string>
     */
    public static function allowedEmails(): array
    {
        /** @var list<string> $emails */
        $emails = config('registration.allowed_emails', []);

        return $emails;
    }

    public static function isAllowed(string $email): bool
    {
        if (! self::isEnabled()) {
            return true;
        }

        return in_array(strtolower(trim($email)), self::allowedEmails(), true);
    }
}
