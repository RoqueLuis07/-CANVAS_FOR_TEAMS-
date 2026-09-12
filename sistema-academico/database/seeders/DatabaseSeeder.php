<?php

namespace Database\Seeders;

use App\Models\Materia;
use App\Models\Matricula;
use App\Models\PeriodoAcademico;
use App\Models\Persona;
use App\Models\PlanEstudio;
use App\Models\Postulacion;
use App\Models\Programa;
use App\Models\User;
use App\Services\InscripcionMateriaService;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;

    /**
     * Seed the application's database con un caso completo, de punta a
     * punta: postulación → admisión → matrícula → alta en materias (tanto
     * predefinida para un alumno nuevo, como manual para uno que continúa).
     */
    public function run(): void
    {
        $admin = User::factory()->create([
            'name' => 'Administrador Académico',
            'email' => 'admin@usil.edu.py',
        ]);

        $programa = Programa::factory()->create([
            'codigo' => 'ING-INF',
            'nombre' => 'Ingeniería en Informática',
            'tipo' => 'grado',
        ]);

        $plan = PlanEstudio::factory()->create([
            'programa_id' => $programa->id,
            'nombre' => 'Plan de Estudio 2026',
            'version' => 1,
        ]);

        // Primer semestre: Matemática I es prerrequisito de Cálculo I.
        $matematicaI = Materia::factory()->primerSemestre()->create([
            'plan_estudio_id' => $plan->id,
            'codigo' => 'MAT-101',
            'nombre' => 'Matemática I',
        ]);
        $introProgramacion = Materia::factory()->primerSemestre()->create([
            'plan_estudio_id' => $plan->id,
            'codigo' => 'INF-101',
            'nombre' => 'Introducción a la Programación',
        ]);
        $calculoI = Materia::factory()->create([
            'plan_estudio_id' => $plan->id,
            'codigo' => 'MAT-201',
            'nombre' => 'Cálculo I',
            'semestre_sugerido' => 2,
            'cupo_maximo' => 2,
        ]);
        $calculoI->prerequisitos()->attach($matematicaI);

        $periodo = PeriodoAcademico::factory()->create([
            'nombre' => '2026-2',
            'estado' => 'inscripciones_abiertas',
        ]);

        $inscripciones = new InscripcionMateriaService;

        // ── Caso 1: alumno nuevo — postulación admitida, materias del
        //    primer semestre predefinidas automáticamente por el
        //    Departamento Académico. ──────────────────────────────────
        $aspiranteNuevo = Persona::factory()->create(['nombre_completo' => 'Ana Benítez']);
        $postulacion = Postulacion::factory()->admitido()->create([
            'persona_id' => $aspiranteNuevo->id,
            'programa_id' => $programa->id,
            'periodo_academico_id' => $periodo->id,
        ]);
        $aspiranteNuevo->update(['tipo' => 'alumno']);
        $matriculaNueva = Matricula::factory()->create([
            'persona_id' => $aspiranteNuevo->id,
            'plan_estudio_id' => $plan->id,
            'periodo_academico_id' => $periodo->id,
            'postulacion_id' => $postulacion->id,
        ]);
        $inscripciones->inscribirPredefinidasAlumnoNuevo($matriculaNueva);

        // ── Caso 2: alumno que continúa — ya aprobó el prerrequisito
        //    (Matemática I) en un período anterior, y ahora da de alta
        //    Cálculo I manualmente, respetando prerrequisitos y cupo. ────
        $alumnoContinua = Persona::factory()->alumno()->create(['nombre_completo' => 'Carlos Rojas']);
        $periodoAnterior = PeriodoAcademico::factory()->create([
            'nombre' => '2026-1',
            'estado' => 'cerrado',
        ]);
        $matriculaAnterior = Matricula::factory()->create([
            'persona_id' => $alumnoContinua->id,
            'plan_estudio_id' => $plan->id,
            'periodo_academico_id' => $periodoAnterior->id,
            'postulacion_id' => null,
            'estado' => 'finalizada',
        ]);
        $matriculaAnterior->inscripciones()->create([
            'materia_id' => $matematicaI->id,
            'origen' => 'manual',
            'estado' => 'aprobada',
            'fecha_inscripcion' => now()->subMonths(6),
        ]);

        $matriculaContinua = Matricula::factory()->create([
            'persona_id' => $alumnoContinua->id,
            'plan_estudio_id' => $plan->id,
            'periodo_academico_id' => $periodo->id,
            'postulacion_id' => null,
        ]);
        $inscripciones->inscribirManual($matriculaContinua, $calculoI);

        $this->command?->info("Seed listo. Login de prueba: {$admin->email}");
    }
}
