import logging
from typing import Any

from app.core.config import settings
from app.services import canvas_client as canvas
from app.services import teams_client as graph
from app.services.credential_generator import generate_credentials, parse_name

logger = logging.getLogger(__name__)

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
            f"/users/{upn}?$select=id,displayName,userPrincipalName,mail,accountEnabled,createdDateTime"
        )
        return True, {
            "found_by": "upn",
            "azure_id": user.get("id"),
            "name": user.get("displayName", ""),
            "upn": user.get("userPrincipalName", ""),
            "mail": user.get("mail", ""),
            "account_enabled": user.get("accountEnabled"),
            "created": user.get("createdDateTime", ""),
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

    for suffix in suffixes:
        creds = generate_credentials(full_name, cedula, domain, collision_suffix=suffix)
        email = creds["email"]
        email_taken = False
        
        # 2. Verificar colisión en Teams
        if platform in ("teams", "both"):
            try:
                exists_teams, _ = await _teams_user_exists(email)
                if exists_teams:
                    email_taken = True
            except Exception as exc:
                logger.warning(f"Error checking Teams for {email}: {exc}")
                
        # 3. Verificar colisión en Canvas
        if platform in ("canvas", "both") and not email_taken:
            try:
                exists_canvas, info = await _canvas_user_exists(cedula, email)
                if exists_canvas and info.get("found_by") == "login_id":
                    email_taken = True
            except Exception as exc:
                logger.warning(f"Error checking Canvas for {email}: {exc}")
                
        if not email_taken:
            return creds, "new"
            
    # Fallback (extremadamente raro que se agoten los 100 sufijos)
    fallback_creds = generate_credentials(full_name, cedula, domain, collision_suffix="x")
    return fallback_creds, "fallback"
