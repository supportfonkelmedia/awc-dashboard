<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;

class AdminSeeder extends Seeder
{
    /**
     * Seed a verified admin user for local/staging (credentials via .env).
     */
    public function run(): void
    {
        $email = env('ADMIN_EMAIL', 'admin@awc-dashboard.nl');
        $name = env('ADMIN_NAME', 'admin');
        $password = env('ADMIN_PASSWORD', 'password');

        User::updateOrCreate(
            ['email' => $email],
            [
                'name' => $name,
                'password' => $password,
                'email_verified_at' => now(),
            ],
        );
    }
}
