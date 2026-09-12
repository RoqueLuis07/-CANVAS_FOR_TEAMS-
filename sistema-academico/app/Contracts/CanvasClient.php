<?php

namespace App\Contracts;

interface CanvasClient
{
    /**
     * Crea un curso en Canvas dentro de la subcuenta configurada.
     *
     * @return string El canvas_course_id creado.
     */
    public function createCourse(string $name, string $sisCourseId): string;

    /**
     * Matricula a un usuario ya existente en Canvas dentro de un curso.
     */
    public function enrollUser(string $canvasCourseId, string $canvasUserId, string $role = 'StudentEnrollment'): void;

    /**
     * Da de baja (concluye) la matrícula de un usuario en un curso.
     */
    public function unenrollUser(string $canvasCourseId, string $canvasUserId): void;
}
