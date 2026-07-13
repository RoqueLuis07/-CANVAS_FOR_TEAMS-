"""Reportes de administración: licencias huérfanas, cuentas inactivas de Teams
y verificación de envío de correo contra el buzón real de Outlook.

Algunos de estos reportes requieren permisos de Azure AD que todavía NO están
concedidos a la app registration (ver detalle en cada endpoint) — devuelven un
error claro hasta que se otorgue el permiso y el admin consent en Azure Portal.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Annotated

from app.services import teams_client as graph

router = APIRouter(prefix="/reports", tags=["Reportes"])


# ── Licencias huérfanas (cuentas deshabilitadas que siguen con licencia) ────

@router.get("/orphaned-licenses", summary="Cuentas deshabilitadas que todavía tienen licencia asignada")
async def orphaned_licenses():
    users = await graph.list_disabled_users_with_licenses()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.get("id"),
                "displayName": u.get("displayName"),
                "userPrincipalName": u.get("userPrincipalName"),
                "licenses": u.get("licenseNames") or [lic.get("skuId") for lic in (u.get("assignedLicenses") or [])],
            }
            for u in users
        ],
    }


class FreeLicensesIn(BaseModel):
    user_ids: list[str]


@router.post("/orphaned-licenses/free", summary="Liberar licencias de las cuentas seleccionadas")
async def free_orphaned_licenses(body: FreeLicensesIn):
    results = {"succeeded": [], "failed": []}
    for uid in body.user_ids:
        try:
            removed = await graph.remove_all_licenses(uid)
            results["succeeded"].append({"id": uid, "removed": removed})
        except Exception as exc:
            results["failed"].append({"id": uid, "error": str(exc)})
    return results


# ── Cuentas de Teams inactivas (requiere AuditLog.Read.All) ────────────────

@router.get("/inactive-teams-users", summary="Cuentas habilitadas sin inicio de sesión reciente")
async def inactive_teams_users(days: Annotated[int, Query(ge=1, le=730)] = 60):
    try:
        users = await graph.get_inactive_users(min_days_inactive=days)
    except HTTPException as exc:
        if exc.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Este reporte requiere el permiso de aplicación 'AuditLog.Read.All' "
                    "con consentimiento de administrador en Azure Portal (App Registrations "
                    "→ API Permissions → Add permission → Microsoft Graph → Application "
                    "permissions → AuditLog.Read.All → Grant admin consent). "
                    f"Detalle original: {exc.detail}"
                ),
            )
        raise
    return {
        "total": len(users),
        "days": days,
        "users": [
            {
                "id": u.get("id"),
                "displayName": u.get("displayName"),
                "userPrincipalName": u.get("userPrincipalName"),
                "last_signin": u.get("last_signin"),
            }
            for u in users
        ],
    }


# ── Actividad de Teams por usuario (requiere Reports.Read.All) ─────────────

@router.get("/teams-activity", summary="Reporte de actividad de Teams por usuario")
async def teams_activity(period: str = "D90"):
    if period not in ("D7", "D30", "D90", "D180"):
        raise HTTPException(status_code=400, detail="period debe ser D7, D30, D90 o D180")
    try:
        rows = await graph.get_teams_activity_report(period=period)
    except HTTPException as exc:
        if exc.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Este reporte requiere el permiso de aplicación 'Reports.Read.All' "
                    "con consentimiento de administrador en Azure Portal. Si ya está "
                    "concedido y sigue fallando, revisar que 'Reports concealment' esté "
                    "desactivado en el Admin Center (Settings → Org settings → Reports) "
                    "para poder ver nombres/UPN reales en vez de datos anonimizados. "
                    f"Detalle original: {exc.detail}"
                ),
            )
        raise
    return {"period": period, "total": len(rows), "rows": rows}


# ── Verificación de envío real (requiere Mail.Read sobre el buzón SMTP) ────

class VerifySentIn(BaseModel):
    to_email: str
    since_iso: str  # ISO 8601 UTC, ej: 2026-07-13T00:00:00Z


@router.post("/verify-email-sent", summary="Confirmar en Outlook (Enviados) si un correo realmente salió")
async def verify_email_sent(body: VerifySentIn):
    try:
        found = await graph.search_sent_email(body.to_email, body.since_iso)
    except HTTPException as exc:
        if exc.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Esta verificación requiere el permiso de aplicación 'Mail.Read' "
                    "(o 'Mail.ReadBasic.All') con consentimiento de administrador, con "
                    "acceso al buzón configurado en SMTP_USER. Otorgarlo en Azure Portal "
                    "→ App Registrations → API Permissions → Add permission → Microsoft "
                    "Graph → Application permissions → Mail.Read → Grant admin consent. "
                    f"Detalle original: {exc.detail}"
                ),
            )
        raise
    return {"to_email": body.to_email, "found_in_sent_items": found}
