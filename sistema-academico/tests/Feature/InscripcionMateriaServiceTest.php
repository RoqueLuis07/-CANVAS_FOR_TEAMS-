<?php

namespace Tests\Feature;

use App\Exceptions\InscripcionMateriaException;
use App\Models\Materia;
use App\Models\Matricula;
use App\Models\PlanEstudio;
use App\Models\Postulacion;
use App\Services\InscripcionMateriaService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class InscripcionMateriaServiceTest extends TestCase
{
    use RefreshDatabase;

    private InscripcionMateriaService $service;

    protected function setUp(): void
    {
        parent::setUp();

        $this->service = new InscripcionMateriaService;
    }

    public function test_no_deja_inscribir_sin_prerequisito_aprobado(): void
    {
        $plan = PlanEstudio::factory()->create();
        $prerequisito = Materia::factory()->create(['plan_estudio_id' => $plan->id]);
        $materia = Materia::factory()->create(['plan_estudio_id' => $plan->id, 'cupo_maximo' => null]);
        $materia->prerequisitos()->attach($prerequisito);

        $matricula = Matricula::factory()->create(['plan_estudio_id' => $plan->id, 'postulacion_id' => null]);

        $this->expectException(InscripcionMateriaException::class);
        $this->expectExceptionMessage('falta aprobar');

        $this->service->inscribirManual($matricula, $materia);
    }

    public function test_deja_inscribir_con_prerequisito_aprobado(): void
    {
        $plan = PlanEstudio::factory()->create();
        $prerequisito = Materia::factory()->create(['plan_estudio_id' => $plan->id]);
        $materia = Materia::factory()->create(['plan_estudio_id' => $plan->id, 'cupo_maximo' => null]);
        $materia->prerequisitos()->attach($prerequisito);

        $matricula = Matricula::factory()->create(['plan_estudio_id' => $plan->id, 'postulacion_id' => null]);
        $matricula->inscripciones()->create([
            'materia_id' => $prerequisito->id,
            'origen' => 'manual',
            'estado' => 'aprobada',
            'fecha_inscripcion' => now(),
        ]);

        $inscripcion = $this->service->inscribirManual($matricula, $materia);

        $this->assertSame('inscrita', $inscripcion->estado);
        $this->assertSame('manual', $inscripcion->origen);
    }

    public function test_no_deja_inscribir_sin_cupo_disponible(): void
    {
        $plan = PlanEstudio::factory()->create();
        $materia = Materia::factory()->create(['plan_estudio_id' => $plan->id, 'cupo_maximo' => 1]);

        $primeraMatricula = Matricula::factory()->create(['plan_estudio_id' => $plan->id, 'postulacion_id' => null]);
        $this->service->inscribirManual($primeraMatricula, $materia);

        $segundaMatricula = Matricula::factory()->create(['plan_estudio_id' => $plan->id, 'postulacion_id' => null]);

        $this->expectException(InscripcionMateriaException::class);
        $this->expectExceptionMessage('No hay cupo disponible');

        $this->service->inscribirManual($segundaMatricula, $materia);
    }

    public function test_no_deja_inscribir_dos_veces_en_la_misma_materia(): void
    {
        $plan = PlanEstudio::factory()->create();
        $materia = Materia::factory()->create(['plan_estudio_id' => $plan->id, 'cupo_maximo' => null]);
        $matricula = Matricula::factory()->create(['plan_estudio_id' => $plan->id, 'postulacion_id' => null]);

        $this->service->inscribirManual($matricula, $materia);

        $this->expectException(InscripcionMateriaException::class);
        $this->expectExceptionMessage('ya está inscrito');

        $this->service->inscribirManual($matricula, $materia);
    }

    public function test_alumno_nuevo_recibe_materias_de_primer_semestre_predefinidas(): void
    {
        $plan = PlanEstudio::factory()->create();
        Materia::factory()->primerSemestre()->create(['plan_estudio_id' => $plan->id]);
        Materia::factory()->primerSemestre()->create(['plan_estudio_id' => $plan->id]);
        Materia::factory()->create(['plan_estudio_id' => $plan->id, 'semestre_sugerido' => 3]);

        $matricula = Matricula::factory()->create([
            'plan_estudio_id' => $plan->id,
            'postulacion_id' => Postulacion::factory()->admitido()->create()->id,
        ]);

        $inscripciones = $this->service->inscribirPredefinidasAlumnoNuevo($matricula);

        $this->assertCount(2, $inscripciones);
        $this->assertTrue($inscripciones->every(fn ($i) => $i->origen === 'predefinida'));
    }

    public function test_alumno_que_continua_no_puede_recibir_materias_predefinidas(): void
    {
        $plan = PlanEstudio::factory()->create();
        $matricula = Matricula::factory()->create(['plan_estudio_id' => $plan->id, 'postulacion_id' => null]);

        $this->expectException(InscripcionMateriaException::class);

        $this->service->inscribirPredefinidasAlumnoNuevo($matricula);
    }
}
