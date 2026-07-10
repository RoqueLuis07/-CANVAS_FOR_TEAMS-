"""Envío de correos de credenciales (SMTP).

Replica el flujo de "Envío de Credenciales" / "Envío de Credenciales UBS"
del proceso manual anterior (referencias_excel/alumnos para crear.xlsm):
el alumno/docente recibe sus credenciales institucionales en su correo
personal, con copia a un conjunto de direcciones institucionales que
depende del tipo de programa.
"""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)

# CC fijo compartido por todos los envíos de credenciales.
_BASE_CC = ["lflorentin@usil.edu.py", "comercialcredenciales@usil.edu.py", "resteche@usil.edu.py"]

# CC adicional según el tipo de programa, replicando "Envio Credenciales"
# (grado) vs "Envio Credenciales UBS" (diplomados) de la planilla de referencia.
_PROGRAM_CC: dict[str, list[str]] = {
    "diplomado": ["ubs@usil.edu.py"],
    "grado": ["gradocredenciales@usil.edu.py"],
}


def default_cc_for_program(program_type: str | None) -> list[str]:
    extra = _PROGRAM_CC.get((program_type or "").strip().lower(), [])
    return [*extra, *_BASE_CC]


def _build_credentials_message(
    *, to_email: str, cc: list[str], full_name: str, login_id: str, password: str,
    program_name: str = "",
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Tus credenciales de acceso institucional — USIL"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    if cc:
        msg["Cc"] = ", ".join(cc)

    programa_line = f"<p><strong>Programa:</strong> {program_name}</p>" if program_name else ""
    html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #222;">
      <p>Hola {full_name},</p>
      <p>Ya tenés acceso a Canvas LMS y Microsoft Teams con las siguientes credenciales institucionales:</p>
      <ul>
        <li><strong>Usuario:</strong> {login_id}</li>
        <li><strong>Contraseña temporal:</strong> {password}</li>
      </ul>
      {programa_line}
      <p>Por seguridad, el sistema te pedirá cambiar la contraseña la primera vez que inicies sesión.</p>
      <p>Saludos,<br>Universidad San Ignacio de Loyola — Área de Tecnologías de la Información</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))
    return msg


def _send_sync(msg: MIMEMultipart, to_addrs: list[str]) -> None:
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=15) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, to_addrs, msg.as_string())


async def send_credentials_email(
    *,
    to_email: str,
    full_name: str,
    login_id: str,
    password: str,
    program_type: str | None = None,
    program_name: str = "",
    extra_cc: list[str] | None = None,
) -> None:
    """Envía el correo de credenciales.

    Lanza RuntimeError si SMTP no está configurado, o la excepción real de
    smtplib si el envío falla — el caller decide cómo reportarlo (nunca debe
    abortar la creación de la cuenta, que ya ocurrió con éxito).
    """
    if not settings.smtp_configured:
        raise RuntimeError(
            "El envío de correo no está configurado (faltan SMTP_SERVER/SMTP_USER/SMTP_PASSWORD)."
        )
    if not to_email or "@" not in to_email:
        raise ValueError("Correo personal inválido o vacío.")

    cc = list(dict.fromkeys([*default_cc_for_program(program_type), *(extra_cc or [])]))
    msg = _build_credentials_message(
        to_email=to_email, cc=cc, full_name=full_name, login_id=login_id,
        password=password, program_name=program_name,
    )
    try:
        await asyncio.to_thread(_send_sync, msg, [to_email, *cc])
    except Exception as exc:
        logger.error("Error enviando correo de credenciales a %s: %s", to_email, exc)
        raise
