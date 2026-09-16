<?php

namespace App\Rules;

use App\Support\RegistrationAllowlist;
use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class AllowedRegistrationEmail implements ValidationRule
{
    /**
     * @param  Closure(string, ?string=): \Illuminate\Translation\PotentiallyTranslatedString  $fail
     */
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if (! is_string($value) || ! RegistrationAllowlist::isAllowed($value)) {
            $fail('This email address is not authorized to register. Contact an administrator.');
        }
    }
}
