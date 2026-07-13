"""Envío de correos de credenciales (SMTP).

Replica el flujo de "Envío de Credenciales" / "Envío de Credenciales UBS"
del proceso manual anterior (referencias_excel/alumnos para crear.xlsm):
el alumno/docente recibe sus credenciales institucionales en su correo
personal, con copia a un conjunto de direcciones institucionales que
depende del tipo de programa.
"""
import asyncio
import logging
import mimetypes
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# CC fijo compartido por todos los envíos de credenciales.
_BASE_CC = ["lflorentin@usil.edu.py", "comercialcredenciales@usil.edu.py", "resteche@usil.edu.py"]

# CC adicional según el tipo de programa, replicando "Envio Credenciales"
# (grado) vs "Envio Credenciales UBS" (diplomados) de la planilla de referencia.
_PROGRAM_CC: dict[str, list[str]] = {
    "diplomado": ["ubs@usil.edu.py", "glezcano@usil.edu.py"],
    "grado": ["gradocredenciales@usil.edu.py"],
}

# Instructivos que el proceso manual anterior adjuntaba a los correos de
# Diplomados (referencias_excel/alumnos para crear.xlsm, hoja "Envio
# Credenciales UBS"). Se mantienen en el repo tal como estaban.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_DIPLOMADO_ATTACHMENTS_DIR = _BACKEND_DIR / "Archivos para los correos" / "Diplomados (UBS - USIL Business School)"
_DIPLOMADO_ATTACHMENTS = [
    _DIPLOMADO_ATTACHMENTS_DIR / "2° Acceso a la Plataforma Teams- Instructivo.pdf",
    _DIPLOMADO_ATTACHMENTS_DIR / "3° Descargar grabacion en TEAMS - Instructivo.pdf",
]

# Datos de contacto de TI UBS, tal como aparecen en el correo real que el
# equipo venía enviando a mano (mismo texto, mismo WhatsApp).
_DIPLOMADO_CONTACT_EMAILS = ["lflorentin@usil.edu.py", "glezcano@usil.edu.py"]
_DIPLOMADO_WHATSAPP = "0991 856 488"
_DIPLOMADO_TEAMS_LINK = "https://teams.cloud.microsoft/"


def default_cc_for_program(program_type: str | None) -> list[str]:
    extra = _PROGRAM_CC.get((program_type or "").strip().lower(), [])
    return [*extra, *_BASE_CC]


def attachments_for_program(program_type: str | None) -> list[Path]:
    """Adjuntos fijos según el tipo de programa (hoy solo Diplomados trae
    instructivos). Si algún archivo no existe en disco, se omite en vez de
    romper el envío del correo."""
    if (program_type or "").strip().lower() != "diplomado":
        return []
    return [p for p in _DIPLOMADO_ATTACHMENTS if p.is_file()]


def _attach_files(msg: MIMEMultipart, attachments: list[Path] | None) -> None:
    for path in attachments or []:
        try:
            ctype, _ = mimetypes.guess_type(path.name)
            maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
            part = MIMEApplication(path.read_bytes(), _subtype=subtype)
            part.add_header("Content-Disposition", "attachment", filename=path.name)
            msg.attach(part)
        except Exception as exc:
            logger.warning("No se pudo adjuntar %s al correo de credenciales: %s", path, exc)


def _build_credentials_message(
    *, to_email: str, cc: list[str], full_name: str, login_id: str, password: str,
    program_name: str = "", attachments: list[Path] | None = None,
) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
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
    body = MIMEMultipart("alternative")
    body.attach(MIMEText(html, "html"))
    msg.attach(body)
    _attach_files(msg, attachments)
    return msg


def _build_diplomado_message(
    *, to_email: str, cc: list[str], full_name: str, login_id: str, password: str,
    program_name: str = "", attachments: list[Path] | None = None,
) -> MIMEMultipart:
    """Réplica exacta del correo que TI UBS venía enviando a mano para
    Diplomados (bienvenida a la USIL Business School, acceso a Microsoft
    Teams, contacto de TI y WhatsApp)."""
    msg = MIMEMultipart("mixed")
    subject_program = program_name or "tu programa"
    msg["Subject"] = f"Credenciales de acceso – {subject_program} – TI UBS"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    if cc:
        msg["Cc"] = ", ".join(cc)

    contact_lines = "".join(
        f'<p style="margin:2px 0;">Correo: <a href="mailto:{addr}">{addr}</a></p>'
        for addr in _DIPLOMADO_CONTACT_EMAILS
    )
    contact_inline = " | ".join(
        f'<a href="mailto:{addr}">{addr}</a>' for addr in _DIPLOMADO_CONTACT_EMAILS
    )
    programa_line = f"Usted se encuentra inscrito en el <strong>{program_name}</strong>." if program_name else ""

    html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #222; line-height: 1.5;">
      <p>Estimado(a) {full_name},</p>
      <p>Le damos la bienvenida a la <strong>USIL Business School (UBS)</strong>.</p>
      <p>{programa_line}</p>

      <div style="border:1px solid #d0d5dd; border-radius:8px; padding:12px 16px; margin:16px 0;">
        <p style="margin:0 0 8px;"><strong>Microsoft Teams</strong> es la plataforma oficial donde podrá acceder a sus clases virtuales, materiales académicos y comunicarse con sus docentes y compañeros.</p>
        <p style="margin:0;">Acceda desde el siguiente enlace:<br><a href="{_DIPLOMADO_TEAMS_LINK}">{_DIPLOMADO_TEAMS_LINK}</a></p>
      </div>

      <p>A continuación, con las siguientes credenciales podrá ingresar a <strong>Microsoft Teams</strong>:</p>

      <div style="border:1px solid #d0d5dd; border-radius:8px; padding:12px 16px; margin:16px 0;">
        <p style="margin:0;"><strong>Usuario:</strong> {login_id}</p>
        <p style="margin:0;"><strong>Contraseña:</strong> {password}</p>
      </div>

      <div style="border:1px solid #d0d5dd; border-radius:8px; padding:12px 16px; margin:16px 0;">
        <p style="margin:0 0 8px;">En caso de inconvenientes con el acceso a Teams, puede contactar al área de Tecnología de la Información (TI):</p>
        {contact_lines}
        <p style="margin:2px 0;">WhatsApp corporativo: {_DIPLOMADO_WHATSAPP}</p>
      </div>

      <p>Adjunto encontrará los instructivos de Teams.</p>
      <p>Quedamos atentos a cualquier consulta relacionada con TI y le deseamos mucho éxito en sus estudios.</p>

      <hr style="border:none; border-top:1px solid #d0d5dd; margin:20px 0;">
      <p style="margin:0;"><strong>Área de Tecnología de la Información (TI UBS)</strong><br>
      USIL Business School – Universidad San Ignacio de Loyola<br>
      Correo: {contact_inline}<br>
      WhatsApp corporativo: {_DIPLOMADO_WHATSAPP}</p>
    </div>
    """
    body = MIMEMultipart("alternative")
    body.attach(MIMEText(html, "html"))
    msg.attach(body)
    _attach_files(msg, attachments)
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
    builder = _build_diplomado_message if (program_type or "").strip().lower() == "diplomado" else _build_credentials_message
    msg = builder(
        to_email=to_email, cc=cc, full_name=full_name, login_id=login_id,
        password=password, program_name=program_name,
        attachments=attachments_for_program(program_type),
    )
    try:
        await asyncio.to_thread(_send_sync, msg, [to_email, *cc])
    except Exception as exc:
        logger.error("Error enviando correo de credenciales a %s: %s", to_email, exc)
        raise
