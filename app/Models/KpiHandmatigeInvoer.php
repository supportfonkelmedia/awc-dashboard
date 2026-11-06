<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class KpiHandmatigeInvoer extends Model
{
    public $incrementing = false;

    protected $keyType = 'string';

    protected $table = 'kpi_handmatige_invoer';

    public $timestamps = false;

    protected $fillable = [
        'id',
        'kpi_code',
        'scope_code',
        'periode_einde',
        'waarde',
        'n',
        'ingevoerd_door',
        'ingevoerd_op',
        'opmerking',
    ];

    protected function casts(): array
    {
        return [
            'periode_einde' => 'date',
            'waarde' => 'float',
            'n' => 'integer',
            'ingevoerd_op' => 'datetime',
        ];
    }
}
