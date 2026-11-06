<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Staging voor kpi_invoer.handmatig (Overdracht) tot Peliqan-write live is.
     * Id-vorm: kpi_code|scope_code|periode_einde
     */
    public function up(): void
    {
        Schema::create('kpi_handmatige_invoer', function (Blueprint $table) {
            $table->string('id')->primary();
            $table->string('kpi_code');
            $table->string('scope_code');
            $table->date('periode_einde');
            $table->decimal('waarde', 16, 4);
            $table->unsignedInteger('n');
            $table->string('ingevoerd_door');
            $table->timestamp('ingevoerd_op')->useCurrent();
            $table->text('opmerking')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('kpi_handmatige_invoer');
    }
};
