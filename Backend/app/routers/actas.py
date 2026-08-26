"""Actas: Servicio Técnico y Entrega de Equipos.

Genera PDFs a partir de los .docx REALES y autorizados (ver
app/services/docx_actas.py + docx_to_pdf.py — se completa una copia del
template y se convierte con LibreOffice, no una reconstrucción visual)
con numeración consecutiva por tipo+año ("0001-2026"), y expone un CRUD
completo sobre el registro de actas generadas — incluyendo la posibilidad
de reemplazar el PDF generado por el PDF ya firmado (escaneado) una vez
que el documento fue firmado en papel.
"""
import logging
from datetime import date

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel

from app.core import actas_db as db
from app.services import docx_actas
from app.services.docx_to_pdf import convertir_docx_a_pdf

router = APIRouter(prefix="/actas", tags=["Actas"])
logger = logging.getLogger(__name__)

_CREATED_BY = "admin"


# ── Servicio Técnico ─────────────────────────────────────────────────────

class ServicioTecnicoIn(BaseModel):
    fecha: str
    hora: str | None = None
    departamento_area: str | None = None
    ubicacion_oficina: str | None = None
    persona_reporta: str | None = None
    tipo_equipo: str | None = None
    tipo_equipo_otro: str | None = None
    marca: str | None = None
    modelo: str | None = None
    nro_serie: str | None = None
    falla_motivo: str | None = None
    trabajo_realizado: str | None = None
    repuestos_insumos: str | None = None
    tecnico_responsable: str | None = None
    encargado_ti_nombre: str | None = None
    encargado_ti_ci: str | None = None
    usuario_nombre: str | None = None
    usuario_ci: str | None = None


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}.pdf"'},
    )


@router.post("/servicio-tecnico/preview", summary="Vista previa del PDF sin guardar")
async def preview_servicio_tecnico(body: ServicioTecnicoIn):
    data = body.model_dump()
    data["numero"] = "VISTA PREVIA — sin guardar"
    pdf_bytes = await convertir_docx_a_pdf(docx_actas.generar_docx_servicio_tecnico(data))
    return _pdf_response(pdf_bytes, "vista_previa_servicio_tecnico")


@router.post("/servicio-tecnico", summary="Crear acta de servicio técnico (asigna número y guarda)")
async def crear_servicio_tecnico(body: ServicioTecnicoIn):
    numero, num_seq, anio = await db.siguiente_numero("servicio_tecnico")
    data = body.model_dump()
    data["numero"] = numero
    pdf_bytes = await convertir_docx_a_pdf(docx_actas.generar_docx_servicio_tecnico(data))
    acta = await db.crear_acta_servicio_tecnico(numero, num_seq, anio, data, pdf_bytes, _CREATED_BY)
    acta.pop("pdf_generado", None)
    acta.pop("pdf_firmado", None)
    return acta


@router.get("/servicio-tecnico", summary="Listar actas de servicio técnico")
async def listar_servicio_tecnico(limit: int = 50, offset: int = 0, search: str = ""):
    return await db.listar_actas_servicio_tecnico(limit=limit, offset=offset, search=search)


@router.get("/servicio-tecnico/{acta_id}", summary="Detalle de una acta de servicio técnico")
async def obtener_servicio_tecnico(acta_id: int):
    acta = await db.obtener_acta_servicio_tecnico(acta_id)
    if not acta:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    acta.pop("pdf_generado", None)
    acta.pop("pdf_firmado", None)
    return acta


@router.put("/servicio-tecnico/{acta_id}", summary="Editar una acta de servicio técnico (regenera el PDF)")
async def editar_servicio_tecnico(acta_id: int, body: ServicioTecnicoIn):
    existing = await db.obtener_acta_servicio_tecnico(acta_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    data = body.model_dump()
    data["numero"] = existing["numero"]
    pdf_bytes = await convertir_docx_a_pdf(docx_actas.generar_docx_servicio_tecnico(data))
    updated = await db.actualizar_acta_servicio_tecnico(acta_id, data, pdf_bytes)
    updated.pop("pdf_generado", None)
    updated.pop("pdf_firmado", None)
    return updated


@router.delete("/servicio-tecnico/{acta_id}", summary="Eliminar una acta de servicio técnico")
async def eliminar_servicio_tecnico(acta_id: int):
    ok = await db.eliminar_acta_servicio_tecnico(acta_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return {"status": "success"}


@router.get("/servicio-tecnico/{acta_id}/pdf", summary="Descargar/ver el PDF de una acta (firmado si existe, si no el generado)")
async def pdf_servicio_tecnico(acta_id: int, variant: str = "auto"):
    acta = await db.obtener_acta_servicio_tecnico(acta_id)
    if not acta:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    pdf_bytes = None
    if variant in ("auto", "firmado") and acta.get("pdf_firmado"):
        pdf_bytes = bytes(acta["pdf_firmado"])
    elif variant == "firmado":
        raise HTTPException(status_code=404, detail="Esta acta todavía no tiene un PDF firmado cargado")
    else:
        pdf_bytes = bytes(acta["pdf_generado"])
    return _pdf_response(pdf_bytes, f"acta_servicio_tecnico_{acta['numero']}")


@router.post("/servicio-tecnico/{acta_id}/firmado", summary="Subir el PDF ya firmado (reemplaza al generado para impresión/consulta)")
async def subir_firmado_servicio_tecnico(acta_id: int, file: UploadFile = File(...)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    content = await file.read()
    updated = await db.subir_pdf_firmado_servicio_tecnico(acta_id, content)
    if not updated:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return {"status": "success", "estado": updated["estado"]}


# ── Entrega de Equipos ───────────────────────────────────────────────────

class EntregaEquipoIn(BaseModel):
    fecha_emision: str
    entrega_nombre: str | None = None
    entrega_ci: str | None = None
    entrega_cargo: str | None = None
    recibe_nombre: str | None = None
    recibe_ci: str | None = None
    recibe_cargo: str | None = None
    insumo: str | None = None
    marca: str | None = None
    modelo: str | None = None
    nro_serie: str | None = None
    especificaciones: str | None = None
    accesorios: list[str] = []
    accesorios_otros: str | None = None
    estado_equipo: str | None = None
    observaciones_entrega: str | None = None
    fecha_devolucion: str | None = None
    motivo_devolucion: str | None = None
    estado_equipo_devolucion: str | None = None
    observaciones_devolucion: str | None = None


@router.post("/entrega-equipo/preview", summary="Vista previa del PDF sin guardar")
async def preview_entrega_equipo(body: EntregaEquipoIn):
    data = body.model_dump()
    data["numero"] = "VISTA PREVIA — sin guardar"
    pdf_bytes = await convertir_docx_a_pdf(docx_actas.generar_docx_entrega_equipo(data))
    return _pdf_response(pdf_bytes, "vista_previa_entrega_equipo")


@router.post("/entrega-equipo", summary="Crear acta de entrega de equipo (asigna número y guarda)")
async def crear_entrega_equipo(body: EntregaEquipoIn):
    numero, num_seq, anio = await db.siguiente_numero("entrega_equipo")
    data = body.model_dump()
    data["numero"] = numero
    pdf_bytes = await convertir_docx_a_pdf(docx_actas.generar_docx_entrega_equipo(data))
    acta = await db.crear_acta_entrega_equipo(numero, num_seq, anio, data, pdf_bytes, _CREATED_BY)
    acta.pop("pdf_generado", None)
    acta.pop("pdf_firmado", None)
    return acta


@router.get("/entrega-equipo", summary="Listar actas de entrega de equipos")
async def listar_entrega_equipo(limit: int = 50, offset: int = 0, search: str = ""):
    return await db.listar_actas_entrega_equipo(limit=limit, offset=offset, search=search)


@router.get("/entrega-equipo/{acta_id}", summary="Detalle de una acta de entrega de equipo")
async def obtener_entrega_equipo(acta_id: int):
    acta = await db.obtener_acta_entrega_equipo(acta_id)
    if not acta:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    acta.pop("pdf_generado", None)
    acta.pop("pdf_firmado", None)
    return acta


@router.put("/entrega-equipo/{acta_id}", summary="Editar una acta de entrega de equipo (regenera el PDF)")
async def editar_entrega_equipo(acta_id: int, body: EntregaEquipoIn):
    existing = await db.obtener_acta_entrega_equipo(acta_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    data = body.model_dump()
    data["numero"] = existing["numero"]
    pdf_bytes = await convertir_docx_a_pdf(docx_actas.generar_docx_entrega_equipo(data))
    updated = await db.actualizar_acta_entrega_equipo(acta_id, data, pdf_bytes)
    updated.pop("pdf_generado", None)
    updated.pop("pdf_firmado", None)
    return updated


@router.delete("/entrega-equipo/{acta_id}", summary="Eliminar una acta de entrega de equipo")
async def eliminar_entrega_equipo(acta_id: int):
    ok = await db.eliminar_acta_entrega_equipo(acta_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return {"status": "success"}


@router.get("/entrega-equipo/{acta_id}/pdf", summary="Descargar/ver el PDF de una acta (firmado si existe, si no el generado)")
async def pdf_entrega_equipo(acta_id: int, variant: str = "auto"):
    acta = await db.obtener_acta_entrega_equipo(acta_id)
    if not acta:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    if variant in ("auto", "firmado") and acta.get("pdf_firmado"):
        pdf_bytes = bytes(acta["pdf_firmado"])
    elif variant == "firmado":
        raise HTTPException(status_code=404, detail="Esta acta todavía no tiene un PDF firmado cargado")
    else:
        pdf_bytes = bytes(acta["pdf_generado"])
    return _pdf_response(pdf_bytes, f"acta_entrega_equipo_{acta['numero']}")


@router.post("/entrega-equipo/{acta_id}/firmado", summary="Subir el PDF ya firmado")
async def subir_firmado_entrega_equipo(acta_id: int, file: UploadFile = File(...)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    content = await file.read()
    updated = await db.subir_pdf_firmado_entrega_equipo(acta_id, content)
    if not updated:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return {"status": "success", "estado": updated["estado"]}
