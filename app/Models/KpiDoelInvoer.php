<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class KpiDoelInvoer extends Model
{
    public $incrementing = false;

    protected $keyType = 'string';

    protected $table = 'kpi_doelen_invoer';

    public $timestamps = false;

    protected $fillable = [
        'id',
        'kpi_code',
        'scope_code',
        'geldig_vanaf',
        'doel',
        'marge_bijna',
        'vastgesteld_door',
        'ingevoerd_op',
        'opmerking',
    ];

    protected function casts(): array
    {
        return [
            'geldig_vanaf' => 'date',
            'doel' => 'float',
            'marge_bijna' => 'float',
            'ingevoerd_op' => 'datetime',
        ];
    }
}
