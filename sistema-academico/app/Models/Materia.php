<?php

namespace App\Models;

use Database\Factories\MateriaFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Materia extends Model
{
    /** @use HasFactory<MateriaFactory> */
    use HasFactory;

    protected $fillable = [
        'plan_estudio_id',
        'codigo',
        'nombre',
        'creditos',
        'semestre_sugerido',
        'cupo_maximo',
        'activa',
    ];

    protected function casts(): array
    {
        return [
            'activa' => 'boolean',
        ];
    }

    public function planEstudio(): BelongsTo
    {
        return $this->belongsTo(PlanEstudio::class);
    }

    /**
     * Materias que esta materia exige como prerrequisito.
     */
    public function prerequisitos(): BelongsToMany
    {
        return $this->belongsToMany(Materia::class, 'materia_prerequisito', 'materia_id', 'prerequisito_id');
    }

    /**
     * Materias para las que esta materia es prerrequisito.
     */
    public function esPrerequisitoDe(): BelongsToMany
    {
        return $this->belongsToMany(Materia::class, 'materia_prerequisito', 'prerequisito_id', 'materia_id');
    }

    public function inscripciones(): HasMany
    {
        return $this->hasMany(InscripcionMateria::class);
    }

    /**
     * Cuántas inscripciones activas (no retiradas) tiene hoy, para
     * validar el cupo máximo antes de dar de alta a un alumno más.
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
