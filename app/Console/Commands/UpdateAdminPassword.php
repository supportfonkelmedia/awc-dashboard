<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Validator;
use Illuminate\Validation\Rules\Password;

final class UpdateAdminPassword extends Command
{
    /**
     * @var string
     */
    protected $signature = 'admin:update-password
                            {email? : Email of the user to update (defaults to ADMIN_EMAIL)}
                            {--password= : New password (omit to enter interactively)}';

    /**
     * @var string
     */
    protected $description = 'Set a new password for an admin user (by email).';

    public function handle(): int
    {
        $email = $this->argument('email') ?: (string) env('ADMIN_EMAIL', 'admin@awc-dashboard.nl');

        /** @var User|null $user */
        $user = User::query()->where('email', $email)->first();

        if ($user === null) {
            $this->components->error("No user found for email: {$email}");

            return self::FAILURE;
        }

        $password = $this->option('password');

        if ($password === null || $password === '') {
            $password = (string) $this->secret('New password');
            $confirm = (string) $this->secret('Confirm new password');

            if ($password === '' || $confirm === '') {
                $this->components->error('Password cannot be empty.');

                return self::FAILURE;
            }

            if (! hash_equals($password, $confirm)) {
                $this->components->error('Passwords do not match.');

                return self::FAILURE;
            }
        }

        $validator = Validator::make(
            ['password' => $password],
            ['password' => ['required', Password::defaults()]],
        );

        if ($validator->fails()) {
            foreach ($validator->errors()->all() as $message) {
                $this->components->error($message);
            }

            return self::FAILURE;
        }

        $user->password = $password;
        $user->save();

        $this->components->info("Password updated for {$user->email}.");

        return self::SUCCESS;
    }
}
