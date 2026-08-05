import logging
import re
import unicodedata
from typing import Any

from app.core.config import settings
from app.services import canvas_client as canvas
from app.services import teams_client as graph
from app.services.credential_generator import generate_credentials, parse_name

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """Normaliza un nombre para comparar sin importar tildes, mayúsculas
    o espacios extra (ej. 'María Pérez' == 'MARIA  PEREZ')."""
    ascii_name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_name.lower().split())


def _normalize_cedula(value: str) -> str:
    """Quita puntos/guiones/espacios de una cédula para poder comparar
    '3.517.784' con '3517784' sin falsos negativos."""
    return re.sub(r"[.\-\s]", "", value or "")

async def _canvas_user_exists(cedula: str, login_id: str) -> tuple[bool, dict]:
    """Verifica si un usuario existe en Canvas por SIS ID (cédula) o login_id.

    Busca primero por SIS user ID (cédula) — encuentra al usuario aunque haya
    cambiado de nombre. Si no lo encuentra, hace fallback por login_id (email
    institucional generado).

    Returns:
        (exists: bool, user_info: dict)
    """
    try:
        user = await canvas.get(f"/users/sis_user_id:{cedula}")
        return True, {
            "found_by": "cedula",
            "canvas_id": user.get("id"),
            "name": user.get("name", ""),
            "login_id": user.get("login_id", ""),
            "email": user.get("email", ""),
        }
    except Exception:
        pass

    try:
        search = await canvas.get(f"/accounts/{settings.canvas_account_id}/users", {"search_term": login_id})
        if isinstance(search, list):
            for u in search:
                if u.get("login_id", "").lower() == login_id.lower():
                    return True, {
                        "found_by": "login_id",
                        "canvas_id": u.get("id"),
                        "name": u.get("name", ""),
                        "login_id": u.get("login_id", ""),
                        "email": u.get("email", ""),
                        # Cédula real (SIS ID) de la cuenta encontrada, si el
                        # search de Canvas la expone — permite la verificación
                        # cruzada por cédula además de por nombre.
                        "cedula": str(u.get("sis_user_id") or "").strip(),
                    }
    except Exception:
        pass

    return False, {}


async def _teams_user_exists(upn: str) -> tuple[bool, dict]:
    """Verifica si un usuario existe en Azure AD por userPrincipalName.

    Returns:
        (exists: bool, user_info: dict)

    Raises:
        Exception si el error no es 404 (problema real de conexión o permisos).
    """
    try:
        user = await graph.get(
            f"/users/{upn}?$select=id,displayName,userPrincipalName,mail,accountEnabled,createdDateTime,postalCode"
        )
        return True, {
            "found_by": "upn",
            "azure_id": user.get("id"),
            "name": user.get("displayName", ""),
            "upn": user.get("userPrincipalName", ""),
            "mail": user.get("mail", ""),
            "account_enabled": user.get("accountEnabled"),
            "created": user.get("createdDateTime", ""),
            # Azure AD no tiene un campo nativo de cédula/documento de
            # identidad — el proceso de alta la guarda en "postalCode"
            # (código postal, reutilizado como campo libre) para poder
            # cruzarla más adelante, igual que el SIS ID en Canvas.
            "cedula": str(user.get("postalCode") or "").strip(),
        }
    except Exception as exc:
        err = str(exc)
        if "404" in err or "Request_ResourceNotFound" in err or "does not exist" in err.lower():
            return False, {}
        raise


async def generate_unique_credentials(full_name: str, cedula: str, platform: str = "both") -> tuple[dict, str]:
    """Genera credenciales asegurando que el correo institucional sea único en la plataforma destino.
    
    Returns:
        (creds, status)
        - status puede ser: "new" (nuevo correo o único), "existing_cedula" (se mantiene porque ya existe en Canvas), etc.
    """
    domain = settings.institutional_domain
    base_creds = generate_credentials(full_name, cedula, domain)
    
    # 1. Verificar si ya existe por cédula en Canvas
    # (Si existe, retenemos su correo, no generamos uno nuevo)
    try:
        if platform in ("canvas", "both"):
            exists, info = await _canvas_user_exists(cedula, base_creds["email"])
            if exists and info.get("found_by") == "cedula":
                # Usamos el correo que tenga en Canvas para Azure también (re-ingreso o actualización)
                if info.get("login_id") and "@" in info.get("login_id"):
                    # Solo reemplazamos email/login_id en base_creds, pero mantenemos el password por defecto
                    login_id = info["login_id"]
                    base_creds["email"] = login_id
                    base_creds["login_id"] = login_id.split("@")[0]
                return base_creds, "existing_cedula"
    except Exception as exc:
        logger.warning(f"Error checking Canvas for {cedula}: {exc}")

    # Lista de sufijos a intentar: "" (vacío), y progresivamente letras de los nombres/apellidos adicionales
    suffixes = [""]
    first, last, extra_words = parse_name(full_name)
    
    for word in extra_words:
        for i in range(1, len(word) + 1):
            cand = word[:i].lower()
            if cand not in suffixes:
                suffixes.append(cand)
                
    # Fallback sin usar números: usar letras del primer nombre si no hay nombres adicionales
    for word in [first, last]:
        for i in range(1, len(word) + 1):
            cand = word[:i].lower()
            if cand not in suffixes:
                suffixes.append(cand)

    collision_with: str | None = None
    collision_cedula_status: str | None = None
    target_cedula = _normalize_cedula(cedula)

    for suffix in suffixes:
        creds = generate_credentials(full_name, cedula, domain, collision_suffix=suffix)
        email = creds["email"]
        email_taken = False
        colliding_name = None
        colliding_cedula = None

        # 2. Verificar colisión en Teams
        if platform in ("teams", "both"):
            try:
                exists_teams, info = await _teams_user_exists(email)
                if exists_teams:
                    email_taken = True
                    colliding_name = info.get("name")
                    colliding_cedula = info.get("cedula")
            except Exception as exc:
                logger.warning(f"Error checking Teams for {email}: {exc}")

        # 3. Verificar colisión en Canvas
        if platform in ("canvas", "both") and not email_taken:
            try:
                exists_canvas, info = await _canvas_user_exists(cedula, email)
                if exists_canvas and info.get("found_by") == "login_id":
                    email_taken = True
                    colliding_name = info.get("name")
                    colliding_cedula = info.get("cedula")
            except Exception as exc:
                logger.warning(f"Error checking Canvas for {email}: {exc}")

        same_name = email_taken and colliding_name and _normalize_name(colliding_name) == _normalize_name(full_name)

        if same_name:
            colliding_cedula_norm = _normalize_cedula(colliding_cedula or "")
            if colliding_cedula_norm and target_cedula and colliding_cedula_norm == target_cedula:
                # Nombre Y cédula (SIS ID en Canvas / postalCode en Azure AD)
                # coinciden exactamente: es la misma persona sin ninguna duda
                # — se reutiliza directamente esa cuenta, no se crea otra.
                creds["reused_reason"] = "Nombre y cédula coinciden exactamente con una cuenta existente"
                return creds, "existing_name"
            if colliding_cedula_norm and target_cedula and colliding_cedula_norm != target_cedula:
                # Mismo nombre pero cédula distinta: son confirmadamente dos
                # personas distintas (no un alias de la misma). Se avisa y se
                # sigue buscando/creando un correo nuevo con otro sufijo.
                if collision_with is None:
                    collision_with = colliding_name
                    collision_cedula_status = "different"
            else:
                # Nombre coincide pero no se pudo verificar por cédula (el
                # campo está vacío en Microsoft/Canvas) — no hay certeza
                # suficiente para reutilizar la cuenta automáticamente, se
                # avisa para que se revise manualmente.
                if collision_with is None:
                    collision_with = colliding_name
                    collision_cedula_status = "unverified"
        elif email_taken and collision_with is None and colliding_name:
            # Guardamos el nombre de la primera colisión encontrada (con el
            # intento sin sufijo) — indica que ya existe OTRA persona con un
            # nombre lo bastante parecido como para generar el mismo correo
            # base. Se lo pasamos al caller para que avise antes de compartir
            # nada manualmente (evita el tipo de confusión "¿esta cuenta es
            # mía o de otra persona con apellido parecido?").
            collision_with = colliding_name

        if not email_taken:
            if collision_with:
                creds["name_collision_with"] = collision_with
                if collision_cedula_status:
                    creds["name_collision_cedula_status"] = collision_cedula_status
            return creds, "new"

    # Fallback (extremadamente raro que se agoten los 100 sufijos)
    fallback_creds = generate_credentials(full_name, cedula, domain, collision_suffix="x")
    if collision_with:
        fallback_creds["name_collision_with"] = collision_with
        if collision_cedula_status:
            fallback_creds["name_collision_cedula_status"] = collision_cedula_status
    return fallback_creds, "fallback"
