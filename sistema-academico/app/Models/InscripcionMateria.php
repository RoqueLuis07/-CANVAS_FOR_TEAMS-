<?php

namespace App\Models;

use Database\Factories\InscripcionMateriaFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class InscripcionMateria extends Model
{
    /** @use HasFactory<InscripcionMateriaFactory> */
    use HasFactory;

    protected $table = 'inscripcion_materias';

    protected $fillable = [
        'matricula_id',
        'materia_id',
        'origen',
        'estado',
        'fecha_inscripcion',
    ];

    protected function casts(): array
    {
        return [
            'fecha_inscripcion' => 'date',
        ];
    }

    public function matricula(): BelongsTo
    {
        return $this->belongsTo(Matricula::class);
    }

    public function materia(): BelongsTo
    {
        return $this->belongsTo(Materia::class);
    }
}
