<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('kpi_feedback', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->nullable()->constrained()->nullOnDelete();
            $table->string('type', 20);
            $table->text('bericht');
            $table->string('scherm', 32);
            $table->string('entiteit', 32)->nullable();
            $table->string('kpi_code', 64)->nullable();
            $table->string('tegel_titel')->nullable();
            $table->string('url', 2048)->nullable();
            $table->string('screenshot_path')->nullable();
            $table->string('status', 20)->default('nieuw')->index();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('kpi_feedback');
    }
};
