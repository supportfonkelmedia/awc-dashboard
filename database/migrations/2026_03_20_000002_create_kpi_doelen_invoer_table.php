<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('kpi_doelen_invoer', function (Blueprint $table) {
            $table->string('id')->primary();
            $table->string('kpi_code');
            $table->string('scope_code');
            $table->date('geldig_vanaf');
            $table->decimal('doel', 16, 4);
            $table->decimal('marge_bijna', 16, 4)->nullable();
            $table->string('vastgesteld_door');
            $table->timestamp('ingevoerd_op')->useCurrent();
            $table->text('opmerking')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('kpi_doelen_invoer');
    }
};
