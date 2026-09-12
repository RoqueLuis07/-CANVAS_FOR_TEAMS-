<?php

namespace App\Models;

use Database\Factories\CursoFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Curso extends Model
{
    /** @use HasFactory<CursoFactory> */
    use HasFactory;

    protected $fillable = [
        'materia_id',
        'periodo_academico_id',
        'cupo_maximo',
        'canvas_course_id',
        'teams_group_id',
        'estado',
    ];

    public function materia(): BelongsTo
    {
        return $this->belongsTo(Materia::class);
    }

    public function periodoAcademico(): BelongsTo
    {
        return $this->belongsTo(PeriodoAcademico::class, 'periodo_academico_id');
    }

    public function inscripciones(): HasMany
    {
        return $this->hasMany(InscripcionMateria::class);
    }

    public function estaCreadoEnCanvas(): bool
    {
        return $this->canvas_course_id !== null;
    }

    public function estaCreadoEnTeams(): bool
    {
        return $this->teams_group_id !== null;
    }

    /**
     * Cuántos cupos quedan libres, contando solo inscripciones activas
     * (no retiradas). Null = sin límite de cupo.
     */
    public function cupoDisponible(): ?int
    {
        if ($this->cupo_maximo === null) {
            return null;
        }

        $ocupados = $this->inscripciones()->where('estado', '!=', 'retirada')->count();

        return max(0, $this->cupo_maximo - $ocupados);
    }
}
