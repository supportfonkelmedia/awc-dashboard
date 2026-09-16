<?php

namespace Tests\Unit;

use App\Support\RegistrationAllowlist;
use Illuminate\Support\Facades\Config;
use Tests\TestCase;

class RegistrationAllowlistTest extends TestCase
{
    public function test_disabled_allowlist_permits_any_email(): void
    {
        Config::set('registration.allowlist_enabled', false);
        Config::set('registration.allowed_emails', []);

        $this->assertTrue(RegistrationAllowlist::isAllowed('anyone@example.com'));
    }

    public function test_enabled_allowlist_permits_listed_email_case_insensitively(): void
    {
        Config::set('registration.allowlist_enabled', true);
        Config::set('registration.allowed_emails', ['alice@example.com']);

        $this->assertTrue(RegistrationAllowlist::isAllowed('Alice@Example.com'));
        $this->assertFalse(RegistrationAllowlist::isAllowed('bob@example.com'));
    }

    public function test_enabled_allowlist_with_empty_list_blocks_everyone(): void
    {
        Config::set('registration.allowlist_enabled', true);
        Config::set('registration.allowed_emails', []);

        $this->assertFalse(RegistrationAllowlist::isAllowed('alice@example.com'));
    }
}
