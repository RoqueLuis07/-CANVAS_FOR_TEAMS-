<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('inscripcion_materias', function (Blueprint $table) {
            $table->id();
            $table->foreignId('matricula_id')->constrained('matriculas')->cascadeOnDelete();
            $table->foreignId('materia_id')->constrained('materias')->cascadeOnDelete();
            // "predefinida": el Departamento Académico la asignó automáticamente
            // (alumno nuevo, primer semestre según el plan de estudio).
            // "manual": el propio alumno/departamento la dio de alta a pedido.
            $table->enum('origen', ['predefinida', 'manual'])->default('manual');
            $table->enum('estado', ['inscrita', 'retirada', 'aprobada', 'reprobada'])->default('inscrita');
            $table->date('fecha_inscripcion');
            $table->timestamps();

            $table->unique(['matricula_id', 'materia_id'], 'inscripcion_unica_por_matricula');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('inscripcion_materias');
    }
};
