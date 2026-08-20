"""Matriculación CPEL por Carrera.

El programa CPEL dicta las mismas materias para 3 carreras (Administración,
Marketing, Negocios Internacionales), pero con una particularidad: en
Canvas existe un curso SEPARADO por carrera para cada materia (ej.
"Administración I (CPEL ADM 2026-02)", "Administración I (CPEL MKT
2026-02)", "Administración I (CPEL NEG 2026-02)"), mientras que en Teams
las 3 carreras comparten UN solo equipo por materia (ej. "Administración I
(CPEL) 2026-02").

Matricular a mano obliga a elegir, para cada alumno, el curso Canvas
correcto entre 3 casi idénticos — este router automatiza esa elección:
dada la carrera y el período, resuelve el curso Canvas específico de cada
materia y el equipo Teams compartido, y matricula a un lote de alumnos
(pegados a mano, sin planilla) en todas las materias seleccionadas.
"""
import asyncio
import json
import logging
import re
import unicodedata

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

CARRERAS = {"ADM": "Administración", "MKT": "Marketing", "NEG": "Negocios Internacionales"}


def _normalize(s: str) -> str:
    ascii_s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return ascii_s.strip().lower()


class MateriaCandidate(BaseModel):
    course_id: str
    course_name: str
    materia_base: str  # nombre de la materia sin el sufijo "(CPEL <CARRERA> <PERIODO>)"


class BuscarMateriasResponse(BaseModel):
    carrera: str
    periodo: str
    materias: list[MateriaCandidate]


@router.get("/materias", response_model=BuscarMateriasResponse, summary="Buscar los cursos de Canvas de una carrera+período CPEL")
async def buscar_materias_cpel(carrera: str, periodo: str):
    carrera = carrera.strip().upper()
    if carrera not in CARRERAS:
        raise HTTPException(status_code=400, detail=f"Carrera inválida: '{carrera}'. Debe ser una de {', '.join(CARRERAS)}.")
    periodo = periodo.strip()
    if not periodo:
        raise HTTPException(status_code=400, detail="Falta el período (ej. 2026-02).")

    try:
        courses = await canvas.paginate(
            f"/accounts/{_ACCOUNT}/courses",
            params={"state[]": ["available", "unpublished", "created", "claimed"]},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener la lista de cursos de Canvas. {e}")

    suffix_pattern = _normalize(f"(cpel {carrera} {periodo})")
    strip_re = re.compile(r"\(\s*cpel\s+" + re.escape(carrera) + r"\s+" + re.escape(periodo) + r"\s*\)", re.IGNORECASE)

    materias: list[MateriaCandidate] = []
    for c in courses or []:
        name = c.get("name") or ""
        if suffix_pattern not in _normalize(name):
            continue
        base = strip_re.sub("", name).strip()
        materias.append(MateriaCandidate(course_id=str(c["id"]), course_name=name, materia_base=base or name))

    materias.sort(key=lambda m: m.materia_base)
    return BuscarMateriasResponse(carrera=carrera, periodo=periodo, materias=materias)


class MateriaSeleccionada(BaseModel):
    course_id: str
    course_name: str
    materia_base: str


class AlumnoCPEL(BaseModel):
    nombre: str
    cedula: str


class CPELEnrollRequest(BaseModel):
    carrera: str
    periodo: str
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

    async def get_team_id(materia_base: str) -> str | None:
        if materia_base in team_id_cache:
            return team_id_cache[materia_base]
        team_name = f"{materia_base} (CPEL) {req.periodo}"
        tid = await graph.search_group_by_name(team_name)
        team_id_cache[materia_base] = tid
        return tid

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

        team_id = await get_team_id(materia.materia_base)
        if not team_id:
            row_errors.append(f"Teams: no se encontró el equipo '{materia.materia_base} (CPEL) {req.periodo}'")
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
