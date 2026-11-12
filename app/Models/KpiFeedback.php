<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class KpiFeedback extends Model
{
    public const TYPES = ['fout', 'verbetering', 'vraag'];

    public const STATUSES = ['nieuw', 'in_behandeling', 'afgerond'];

    protected $table = 'kpi_feedback';

    protected $fillable = [
        'user_id',
        'type',
        'bericht',
        'scherm',
        'entiteit',
        'kpi_code',
        'tegel_titel',
        'url',
        'screenshot_path',
        'status',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
