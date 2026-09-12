<?php

namespace App\Services;

use App\Exceptions\InscripcionMateriaException;
use App\Models\InscripcionMateria;
use App\Models\Materia;
use App\Models\Matricula;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\DB;

/**
 * Reglas de negocio del alta en materias ("inscripción a cursos"):
 *
 *  - Un alumno nuevo (matrícula originada en una postulación admitida) recibe
 *    las materias del primer semestre de su plan de estudio ya predefinidas
 *    por el Departamento Académico — no las elige.
 *  - Un alumno que continúa (matrícula sin postulación de origen) da de alta
 *    sus materias manualmente, sujeto a prerrequisitos y cupo.
 */
class InscripcionMateriaService
{
    /**
     * Da de alta manualmente a un alumno en una materia, validando
     * prerrequisitos y cupo disponible.
     *
     * @throws InscripcionMateriaException
     */
    public function inscribirManual(Matricula $matricula, Materia $materia): InscripcionMateria
    {
        $this->assertPrerequisitosCumplidos($matricula, $materia);
        $this->assertCupoDisponible($materia);
        $this->assertNoInscritaAun($matricula, $materia);

        return DB::transaction(fn () => InscripcionMateria::create([
            'matricula_id' => $matricula->id,
            'materia_id' => $materia->id,
            'origen' => 'manual',
            'estado' => 'inscrita',
            'fecha_inscripcion' => now(),
        ]));
    }

    /**
     * Da de alta al Departamento Académico las materias del primer semestre
     * del plan de estudio para un alumno nuevo. No valida prerrequisitos
     * (un alumno nuevo no puede tenerlos aprobados) ni cupo — el Departamento
     * es responsable de que la oferta alcance para los alumnos admitidos.
     *
     * @return Collection<int, InscripcionMateria>
     */
    public function inscribirPredefinidasAlumnoNuevo(Matricula $matricula): Collection
    {
        if (! $matricula->esDeAlumnoNuevo()) {
            throw new InscripcionMateriaException(
                'Esta matrícula no corresponde a un alumno nuevo: las materias deben darse de alta manualmente.'
            );
        }

        $materiasPrimerSemestre = $matricula->planEstudio
            ->materias()
            ->where('semestre_sugerido', 1)
            ->where('activa', true)
            ->get();

        return DB::transaction(function () use ($matricula, $materiasPrimerSemestre) {
            return $materiasPrimerSemestre->map(fn (Materia $materia) => InscripcionMateria::firstOrCreate(
                ['matricula_id' => $matricula->id, 'materia_id' => $materia->id],
                ['origen' => 'predefinida', 'estado' => 'inscrita', 'fecha_inscripcion' => now()],
            ));
        });
    }

    /**
     * @throws InscripcionMateriaException
     */
    protected function assertPrerequisitosCumplidos(Matricula $matricula, Materia $materia): void
    {
        $prerequisitoIds = $materia->prerequisitos()->pluck('materias.id');

        if ($prerequisitoIds->isEmpty()) {
            return;
        }

        $aprobadasIds = InscripcionMateria::query()
            ->whereHas('matricula', fn ($q) => $q->where('persona_id', $matricula->persona_id))
            ->where('estado', 'aprobada')
            ->whereIn('materia_id', $prerequisitoIds)
            ->pluck('materia_id');

        $faltantes = $prerequisitoIds->diff($aprobadasIds);

        if ($faltantes->isNotEmpty()) {
            $nombres = Materia::whereIn('id', $faltantes)->pluck('nombre')->implode(', ');

            throw new InscripcionMateriaException(
                "No se puede inscribir en \"{$materia->nombre}\": falta aprobar el/los prerrequisito(s) {$nombres}."
            );
        }
    }

    /**
     * @throws InscripcionMateriaException
     */
    protected function assertCupoDisponible(Materia $materia): void
    {
        $disponible = $materia->cupoDisponible();

        if ($disponible !== null && $disponible <= 0) {
            throw new InscripcionMateriaException(
                "No hay cupo disponible en \"{$materia->nombre}\"."
            );
        }
    }

    /**
     * @throws InscripcionMateriaException
     */
    protected function assertNoInscritaAun(Matricula $matricula, Materia $materia): void
    {
        $yaInscrita = InscripcionMateria::query()
            ->where('matricula_id', $matricula->id)
            ->where('materia_id', $materia->id)
            ->where('estado', '!=', 'retirada')
            ->exists();

        if ($yaInscrita) {
            throw new InscripcionMateriaException(
                "El alumno ya está inscrito en \"{$materia->nombre}\" en este período."
            );
        }
    }
}
