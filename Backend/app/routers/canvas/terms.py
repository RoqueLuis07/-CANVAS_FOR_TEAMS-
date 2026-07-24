import asyncio
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.config import settings
from app.services import canvas_client as canvas

router = APIRouter(prefix="/canvas/terms", tags=["Canvas · Terms"])
_ACCOUNT = settings.canvas_account_id


@router.get("", summary="Listar periodos / términos de la cuenta")
async def list_terms(
    search_term: Annotated[str | None, Query()] = None,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
):
    params: dict = {"per_page": per_page}
    if search_term:
        params["search_term"] = search_term
    # Canvas envuelve la respuesta como {"enrollment_terms": [...]} en vez de
    # devolver un array plano — canvas.paginate() no lo puede aplanar solo,
    # así que cada página llega como un dict individual que hay que desempacar.
    pages = await canvas.paginate(f"/accounts/{_ACCOUNT}/terms", params)
    terms: list = []
    for page in pages:
        if isinstance(page, dict):
            terms.extend(page.get("enrollment_terms", []))
        elif isinstance(page, list):
            terms.extend(page)
    return terms


# ── Liberar SIS ID de períodos eliminados que bloquean su reuso ────────────────
#
# Igual que con los cursos: Canvas no libera el sis_term_id cuando un período
# se elimina (soft-delete). El período desaparece de los listados normales,
# pero sigue reservando ese SIS ID y bloquea crear un período nuevo con el
# mismo ID (típico al recrear un período académico).

class ReleaseTermSisIdResolveRequest(BaseModel):
    entries: list[str]


@router.post("/release-sis-id/resolve", summary="Resolver períodos por SIS ID o ID de Canvas (previsualización)")
async def resolve_release_term_sis_id(req: ReleaseTermSisIdResolveRequest):
    seen: set[str] = set()

    async def resolve_one(raw: str):
        entry = raw.strip()
        if not entry or entry in seen:
            return None
        seen.add(entry)

        term = None
        try:
            term = await canvas.get(f"/accounts/{_ACCOUNT}/terms/sis_term_id:{entry}")
        except Exception:
            pass
        if not term:
            try:
                term = await canvas.get(f"/accounts/{_ACCOUNT}/terms/{entry}")
            except Exception:
                pass

        if not term:
            return {"input": entry, "term_id": None, "name": None, "current_sis_id": None,
                    "workflow_state": None, "found": False}

        return {
            "input": entry,
            "term_id": str(term.get("id")),
            "name": term.get("name"),
            "current_sis_id": term.get("sis_term_id"),
            "workflow_state": term.get("workflow_state"),
            "found": True,
        }

    results = await asyncio.gather(*(resolve_one(e) for e in req.entries))
    return [r for r in results if r is not None]


class ReleaseTermSisIdRequest(BaseModel):
    term_ids: list[str]


@router.post("/release-sis-id", summary="Liberar el SIS ID de una lista de períodos (sin tocar sus cursos)")
async def release_term_sis_id(req: ReleaseTermSisIdRequest):
    result = {"succeeded": [], "failed": []}

    for tid in req.term_ids:
        name = f"Período {tid}"
        try:
            term = await canvas.get(f"/accounts/{_ACCOUNT}/terms/{tid}")
            name = term.get("name", name)
        except Exception as e:
            result["failed"].append({"term_id": tid, "name": name, "error": f"No se pudo obtener el período: {e}"})
            continue

        try:
            await canvas.put(f"/accounts/{_ACCOUNT}/terms/{tid}", {"enrollment_term": {"sis_term_id": ""}})
            result["succeeded"].append({"term_id": tid, "name": name})
        except Exception as e:
            result["failed"].append({"term_id": tid, "name": name, "error": str(e)})

    return result
