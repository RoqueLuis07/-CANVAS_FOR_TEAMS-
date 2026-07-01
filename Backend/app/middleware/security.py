from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from urllib.parse import urlparse

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. CSRF Protection for state-mutating methods
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            # Only enforce CSRF if the request uses cookie-based authentication
            if "usil_auth" in request.cookies:
                origin = request.headers.get("origin")
                referer = request.headers.get("referer")
                
                valid_origin = False
                expected_host = urlparse(settings.site_url).netloc
                
                if origin:
                    parsed_origin = urlparse(origin)
                    if parsed_origin.netloc == expected_host:
                        valid_origin = True
                elif referer:
                    parsed_referer = urlparse(referer)
                    if parsed_referer.netloc == expected_host:
                        valid_origin = True
                        
                if not valid_origin and expected_host not in ("localhost:3000", "127.0.0.1:3000"):
                    # Reject request if origin mismatch in production
                    return Response("CSRF Validation Failed", status_code=403)

        # 2. Process Request
        response = await call_next(request)

        # 3. Inject Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Basic CSP: Allow self, inline scripts/styles (for UI), and specific CDNs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://login.microsoftonline.com;"
        )
        response.headers["Content-Security-Policy"] = csp

        return response
