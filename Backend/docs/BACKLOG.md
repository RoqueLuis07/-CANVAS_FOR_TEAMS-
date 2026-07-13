# Backlog — Mejoras evaluadas, no implementadas todavía

Ideas discutidas y explícitamente pospuestas por decisión del equipo. Se dejan
documentadas acá para no perderlas de vista, no como compromiso de fecha.

## Reconciliación automática Canvas ↔ Teams para cuentas de una sola plataforma

Hoy la lógica de "verificar membresía y agregar si falta" (usada en Diplomados)
asume que un alumno puede requerir ambas plataformas. Falta contemplar el caso
de alumnos que institucionalmente solo necesitan Canvas *o* solo Teams, sin que
la reconciliación intente agregarlos a la plataforma que no corresponde.
Pendiente hasta que ese caso de uso exista en la práctica.

## Auto-archivado de cursos/equipos al finalizar el período

Concluir cursos de Canvas y archivar equipos de Teams automáticamente al pasar
la fecha de término de un programa. Decidido no tocar esto por ahora.

## Detección de drift Canvas ↔ Azure AD para cuentas de una sola plataforma

Cruzar cuentas por cédula/email para detectar inconsistencias, pero
contemplando que hay alumnos que legítimamente solo tienen cuenta en una de
las dos plataformas (no todos deben tener ambas).

## Jobs programados (cron)

No hay ningún scheduler corriendo hoy (nada de cron/APScheduler en el
backend); todo se dispara manualmente. Cuando se implemente alguno de los
puntos anteriores que requiere periodicidad real (por ejemplo, reconciliación
o detección de drift), esta es la pieza de infraestructura que falta. Railway
soporta cron jobs nativos — sería el camino más simple.

## Automatización "sin Excel"

El cuello de botella estructural del sistema sigue siendo que toda la carga
de datos institucional depende de planillas Excel manuales (no hay un SIS con
API propia todavía). Mientras eso no cambie institucionalmente, el sistema
seguirá dependiendo de que alguien exporte y suba un archivo. No es algo que
se pueda resolver solo del lado de este webservice.
