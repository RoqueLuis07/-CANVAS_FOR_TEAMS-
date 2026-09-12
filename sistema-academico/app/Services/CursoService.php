<?php

namespace App\Services;

use App\Contracts\CanvasClient;
use App\Contracts\TeamsClient;
use App\Exceptions\CursoException;
use App\Models\Curso;

/**
 * "Asignación de curso": convierte la oferta de una Materia en un Período
 * (un Curso, todavía solo un registro académico) en un curso real de Canvas
 * y un equipo real de Teams. Es el paso que el Departamento Académico
 * dispara antes de poder matricular alumnos en él.
 */
class CursoService
{
    public function __construct(
        protected CanvasClient $canvas,
        protected TeamsClient $teams,
    ) {}

    /**
     * @throws CursoException
     */
    public function crearEnCanvas(Curso $curso): Curso
    {
        if ($curso->estaCreadoEnCanvas()) {
            return $curso;
        }

        $materia = $curso->materia;
        $sisCourseId = "{$materia->codigo}-{$curso->periodo_academico_id}";

        try {
            $canvasCourseId = $this->canvas->createCourse($materia->nombre, $sisCourseId);
        } catch (\Throwable $e) {
            throw new CursoException("No se pudo crear el curso en Canvas: {$e->getMessage()}", previous: $e);
        }

        $curso->update(['canvas_course_id' => $canvasCourseId]);

        return $curso->refresh();
    }

    /**
     * @throws CursoException
     */
    public function crearEnTeams(Curso $curso): Curso
    {
        if ($curso->estaCreadoEnTeams()) {
            return $curso;
        }

        try {
            $teamsGroupId = $this->teams->createTeam($curso->materia->nombre);
        } catch (\Throwable $e) {
            throw new CursoException("No se pudo crear el equipo en Teams: {$e->getMessage()}", previous: $e);
        }

        $curso->update(['teams_group_id' => $teamsGroupId]);

        return $curso->refresh();
    }
}
