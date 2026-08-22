"""Matriculación CPEL por Carrera.

El programa CPEL dicta las mismas materias para 3 carreras (Administración,
Marketing, Negocios), pero con dos particularidades:

1. En Canvas, cada carrera tiene su propia SUBCUENTA (no solo un sufijo en
   el nombre): la jerarquía real es
   Cuenta raíz > <Período, ej. "2026-2"> > CPEL > <Administración|Marketing|Negocios>,
   y los cursos de esa carrera viven directamente adentro de esa subcuenta.
   La API de Canvas para "listar cursos de una cuenta" NO busca recursivo
   en subcuentas hijas — hay que apuntar directo a la subcuenta de la
   carrera, no se puede filtrar por período con un simple search_term en
   la cuenta raíz (eso fue un intento anterior que no encontraba nada).
2. En Teams, las 3 carreras comparten un solo equipo por materia — el
   nombre del curso en Canvas trae el período embebido al final (ej.
   "Administración I (CPEL ADM 2026-02)"), del que se puede derivar el
   nombre del equipo compartido ("Administración I (CPEL) 2026-02") sin
   pedirle el período al usuario por separado.
"""
import asyncio
import json
import logging
import re

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core import jobs
from app.services import canvas_client as canvas
from app.services import teams_client as graph
from app.routers.sync import resolve_user_identities

router = APIRouter(prefix="/cpel", tags=["Matriculación CPEL por Carrera"])
logger = logging.getLogger(__name__)
_ACCOUNT = settings.canvas_account_id

# Suffix esperado al final del nombre del curso: "(CPEL <CODIGO CARRERA> <PERIODO>)".
# Captura el período para poder derivar el nombre del equipo de Teams
# compartido sin pedírselo al usuario por separado.
_SUFFIX_RE = re.compile(r"\(\s*cpel\s+[a-zA-Z]+\s+([^\)]+?)\s*\)\s*$", re.IGNORECASE)


class SubaccountNode(BaseModel):
    id: str
    name: str
    parent_account_id: str | None = None


@router.get("/subaccounts", response_model=list[SubaccountNode], summary="Árbol completo de subcuentas de Canvas")
async def listar_subcuentas():
    """Devuelve TODAS las subcuentas (recursivo) para que el frontend arme
    los 3 selects en cascada (Período > Programa > Carrera) navegando la
    jerarquía real, en vez de adivinar nombres/formatos de período."""
    try:
        data = await canvas.paginate(
            f"/accounts/{_ACCOUNT}/sub_accounts", params={"recursive": "true", "per_page": 100},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener el árbol de subcuentas de Canvas. {e}")

    return [
        SubaccountNode(
            id=str(sa["id"]),
            name=sa.get("name") or "",
            parent_account_id=str(sa["parent_account_id"]) if sa.get("parent_account_id") else None,
        )
        for sa in (data or [])
    ]


class MateriaCandidate(BaseModel):
    course_id: str
    course_name: str
    materia_base: str
    periodo: str | None = None  # None si el nombre del curso no sigue el patrón "(CPEL <CARRERA> <PERIODO>)"


class BuscarMateriasResponse(BaseModel):
    materias: list[MateriaCandidate]


@router.get("/materias", response_model=BuscarMateriasResponse, summary="Cursos de Canvas dentro de la subcuenta de una carrera")
async def buscar_materias_cpel(subaccount_id: str):
    try:
        courses = await canvas.paginate(
            f"/accounts/{subaccount_id}/courses",
            params={"state[]": ["available", "unpublished", "created", "claimed"]},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener los cursos de esa subcuenta. {e}")

    materias: list[MateriaCandidate] = []
    for c in courses or []:
        name = c.get("name") or ""
        m = _SUFFIX_RE.search(name)
        periodo = m.group(1).strip() if m else None
        base = _SUFFIX_RE.sub("", name).strip() if m else name
        materias.append(MateriaCandidate(course_id=str(c["id"]), course_name=name, materia_base=base or name, periodo=periodo))

    materias.sort(key=lambda m: m.materia_base)
    return BuscarMateriasResponse(materias=materias)


class MateriaSeleccionada(BaseModel):
    course_id: str
    course_name: str
    materia_base: str
    periodo: str | None = None


class AlumnoCPEL(BaseModel):
    nombre: str
    cedula: str


class CPELEnrollRequest(BaseModel):
    carrera_label: str = ""  # solo informativo, para el historial de trabajos
    materias: list[MateriaSeleccionada]
    alumnos: list[AlumnoCPEL]


MAX_CPEL_ENROLL = 500  # tope de seguridad sobre alumnos × materias combinado


@router.post("/enroll", summary="Matricular un lote de alumnos de una carrera en las materias CPEL seleccionadas")
async def enroll_cpel(req: CPELEnrollRequest, bg_tasks: BackgroundTasks) -> dict:
    if not req.materias:
        raise HTTPException(status_code=400, detail="No seleccionaste ninguna materia.")
    if not req.alumnos:
        raise HTTPException(status_code=400, detail="No cargaste ningún alumno.")

    total_ops = len(req.materias) * len(req.alumnos)
    if total_ops > MAX_CPEL_ENROLL:
        raise HTTPException(
            status_code=400,
            detail=f"Demasiadas matrículas a la vez ({len(req.alumnos)} alumnos × {len(req.materias)} materias = {total_ops}). Máximo {MAX_CPEL_ENROLL}. Dividí en tandas más chicas.",
        )

    job_id = await jobs.create_job(job_type="cpel_carrera_masivo", operation="import", username="admin")
    bg_tasks.add_task(_process_cpel_enroll_bg, job_id, req)
    return {"status": "success", "job_id": job_id, "message": "Matriculación CPEL iniciada en segundo plano."}


async def _process_cpel_enroll_bg(job_id: int, req: CPELEnrollRequest):
    await jobs.start_job(job_id)

    success_count = 0
    error_count = 0
    results: list[dict] = []

    # El equipo de Teams es compartido entre las 3 carreras (mismo nombre
    # base, sin sufijo de carrera) — se resuelve UNA sola vez por materia,
    # no una vez por alumno, para no repetir la misma búsqueda cientos de
    # veces.
    team_id_cache: dict[str, str | None] = {}

    async def get_team_id(materia: MateriaSeleccionada) -> tuple[str | None, str]:
        team_name = f"{materia.materia_base} (CPEL) {materia.periodo}" if materia.periodo else f"{materia.materia_base} (CPEL)"
        if team_name in team_id_cache:
            return team_id_cache[team_name], team_name
        tid = await graph.search_group_by_name(team_name)
        team_id_cache[team_name] = tid
        return tid, team_name

    async def process_one(alumno: AlumnoCPEL, materia: MateriaSeleccionada):
        nonlocal success_count, error_count
        try:
            canvas_user_id, teams_upn = await resolve_user_identities(alumno.cedula)
        except Exception as e:
            error_count += 1
            results.append({"alumno": alumno.nombre, "materia": materia.materia_base, "status": f"❌ {e}"})
            return

        row_errors = []
        try:
            await canvas.post(f"/courses/{materia.course_id}/enrollments", {
                "enrollment": {
                    "user_id": canvas_user_id,
                    "type": "StudentEnrollment",
                    "enrollment_state": "active",
                    "notify": False,
                },
            })
        except Exception as e:
            msg = str(e)
            if "already" not in msg.lower() and "enrolled" not in msg.lower():
                row_errors.append(f"Canvas: {msg}")

        team_id, team_name = await get_team_id(materia)
        if not team_id:
            row_errors.append(f"Teams: no se encontró el equipo '{team_name}' — revisar el nombre en Teams")
        else:
            try:
                await graph.post(f"/teams/{team_id}/members", {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": [],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{teams_upn}')",
                })
            except Exception as e:
                err_str = str(e).lower()
                if "already exist" not in err_str and "request_badrequest" not in err_str:
                    row_errors.append(f"Teams: {e}")

        if row_errors:
            error_count += 1
            results.append({"alumno": alumno.nombre, "materia": materia.materia_base, "status": f"❌ {' | '.join(row_errors)}"})
        else:
            success_count += 1
            results.append({"alumno": alumno.nombre, "materia": materia.materia_base, "status": "✅ OK"})

    pairs = [(a, m) for a in req.alumnos for m in req.materias]
    batch_size = 5
    for i in range(0, len(pairs), batch_size):
        chunk = pairs[i:i + batch_size]
        await asyncio.gather(*(process_one(a, m) for a, m in chunk))
        await jobs.update_job_progress(
            job_id, success_count, error_count,
            data_json=json.dumps({"total_to_process": len(pairs), "processed": success_count + error_count, "results": results}),
        )

    if error_count and success_count == 0:
        await jobs.fail_job(job_id, f"Todas las matrículas fallaron ({error_count}).")
    else:
        await jobs.complete_job(job_id, success_count, error_count)
