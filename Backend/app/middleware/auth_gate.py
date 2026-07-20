"""Exige sesión válida (usuario en ADMIN_ALLOWED_EMAILS) para todo el
sistema, salvo el propio flujo de login y un puñado de rutas públicas.

Sin esto, las páginas /ui/* y los endpoints de la API quedaban accesibles
sin iniciar sesión — cualquiera con la URL podía crear/eliminar cuentas de
Canvas y Teams sin autenticarse."""
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services import auth as auth_service

# Rutas exactas que deben quedar accesibles sin sesión.
_PUBLIC_PATHS = {
    "/auth/login",
    "/auth/callback",
    "/auth/logout",
    "/ui/login",
    "/health",
    "/ping",
}

# Prefijos públicos (archivos estáticos).
_PUBLIC_PREFIXES = ("/static/",)


def _is_public(path: str) -> bool:
    return path in _PUBLIC_PATHS or path.startswith(_PUBLIC_PREFIXES)


class AuthGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS" or _is_public(path):
            return await call_next(request)

        user = auth_service.get_user_from_request(request)
        if not user:
            if path.startswith("/ui") or path == "/":
                return RedirectResponse(url="/ui/login", status_code=302)
            return JSONResponse(
                status_code=401,
                content={"detail": "No autenticado. Iniciá sesión en /ui/login."},
            )

        return await call_next(request)
