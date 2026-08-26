"""Convierte un .docx (bytes) a PDF invocando LibreOffice en modo headless
— es la única forma de producir un PDF que sea *literalmente* el .docx
autorizado (mismas fuentes, espaciados, layout exactos) en vez de una
reconstrucción aproximada.

Requiere el binario `soffice` disponible en el servidor — ver el
Dockerfile en la raíz del repo, que lo instala explícitamente porque no
viene por defecto en hosting administrado (Railway/Render/Heroku-style).
"""
import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import HTTPException

logger = logging.getLogger(__name__)

_SOFFICE_BIN = shutil.which("soffice") or shutil.which("libreoffice")


async def convertir_docx_a_pdf(docx_bytes: bytes, timeout: int = 60) -> bytes:
    if not _SOFFICE_BIN:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo generar el PDF: LibreOffice no está instalado en este servidor "
                "(necesario para producir el documento exacto a la plantilla autorizada). "
                "Verificá el despliegue — ver Dockerfile."
            ),
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        docx_path = tmp_path / "acta.docx"
        docx_path.write_bytes(docx_bytes)

        # Perfil de usuario aislado por conversión: dos invocaciones de
        # soffice en simultáneo comparten por defecto el mismo perfil y
        # chocan con un lock ("no se puede conectar"), rompiendo la
        # segunda conversión concurrente.
        profile_dir = tmp_path / "profile"
        proc = await asyncio.create_subprocess_exec(
            _SOFFICE_BIN, "--headless", "--norestore",
            f"-env:UserInstallation=file://{profile_dir}",
            "--convert-to", "pdf", "--outdir", str(tmp_path), str(docx_path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(status_code=500, detail="La conversión a PDF tardó demasiado (LibreOffice no respondió).")

        pdf_path = tmp_path / "acta.pdf"
        if proc.returncode != 0 or not pdf_path.exists():
            logger.error(f"soffice convert-to pdf falló (code={proc.returncode}): {stderr.decode(errors='replace')}")
            raise HTTPException(status_code=500, detail="No se pudo convertir el documento a PDF.")

        return pdf_path.read_bytes()
