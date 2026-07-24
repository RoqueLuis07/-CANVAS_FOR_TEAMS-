"""Microsoft Teams team/group management endpoints."""
import asyncio
import re
import time
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.teams import (
    BulkResult,
    BulkTeamsMemberAdd,
    BulkTeamsEmailAdd,
    BulkTeamsMemberRemove,
    TeamsChannelCreate,
    TeamsTeamUpdate,
)
from app.services import teams_client as graph
from app.services.teams_client import create_team_via_group

router = APIRouter(prefix="/teams/teams", tags=["Teams · Teams"])

# Template OData types used by the Teams provisioning API
_TEMPLATES = {
    "standard": "https://graph.microsoft.com/v1.0/teamsTemplates('standard')",
    "educationClass": "https://graph.microsoft.com/v1.0/teamsTemplates('educationClass')",
    "educationStaff": "https://graph.microsoft.com/v1.0/teamsTemplates('educationStaff')",
    "educationProfessionalLearningCommunity": "https://graph.microsoft.com/v1.0/teamsTemplates('educationProfessionalLearningCommunity')",
}


@router.get("", summary="Listar todos los Teams del tenant")
async def list_teams(
    search_term: Annotated[str | None, Query(description="Buscar por displayName")] = None,
    top: Annotated[int, Query(ge=1, le=999)] = 50,
):
    # Base filter for Teams
    filter_query = "resourceProvisioningOptions/Any(x:x eq 'Team')"
    
    if search_term:
        # Avoid injection by removing quotes
        clean_term = search_term.replace("'", "")
        # Note: startswith is supported by Microsoft Graph for displayName
        filter_query = f"{filter_query} and startswith(displayName, '{clean_term}')"

    params = {
        "$top": top,
        "$select": "id,displayName,description,visibility,createdDateTime",
        "$filter": filter_query,
    }
    return await graph.paginate("/groups", params)


class TeamsTeamCreateSimple(BaseModel):
    display_name: str
    description: str | None = None
    visibility: Literal["Public", "Private", "HiddenMembership"] = "Private"
    owner_id: str = Field(..., description="Azure object ID del propietario")
    template: str | None = None


@router.post("", summary="Crear un Team nuevo")
async def create_team(body: TeamsTeamCreateSimple):
    nickname = graph.safe_mail_nickname(body.display_name)
    try:
        return await create_team_via_group(
            display_name=body.display_name,
            mail_nickname=nickname,
            description=body.description or "",
            visibility=body.visibility,
            owner_ids=[body.owner_id],
        )
    except StarletteHTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{team_id}", summary="Obtener Team por ID")
async def get_team(team_id: str):
    try:
        return await graph.get(f"/teams/{team_id}")
    except StarletteHTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))




@router.patch("/{team_id}", summary="Actualizar Team")
async def update_team(team_id: str, body: TeamsTeamUpdate):
    fields = body.model_dump(exclude_none=True)
    mapping = {"display_name": "displayName", "description": "description", "visibility": "visibility"}
    payload = {mapping[k]: v for k, v in fields.items() if k in mapping}
    try:
        return await graph.patch(f"/teams/{team_id}", payload)
    except StarletteHTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{team_id}", summary="Eliminar Team")
async def delete_team(team_id: str):
    try:
        await graph.delete(f"/groups/{team_id}")
        return {"deleted": team_id}
    except StarletteHTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── Eliminación masiva por ID o nombre ─────────────────────────────────────────

_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


class TeamsResolveRequest(BaseModel):
    entries: list[str] = Field(..., description="IDs de grupo/Team o nombres de equipo, uno por entrada")


@router.post("/resolve", summary="Resolver Teams por ID o nombre (previsualización antes de eliminar)")
async def resolve_teams(req: TeamsResolveRequest):
    """Acepta una mezcla de IDs de grupo/Team y nombres de equipo, y devuelve
    para cada entrada si se encontró el equipo real y su ID/nombre resuelto —
    para que el usuario confirme antes de eliminar en lote."""
    seen: set[str] = set()

    async def resolve_one(raw: str):
        entry = raw.strip()
        if not entry or entry in seen:
            return None
        seen.add(entry)

        if _UUID_RE.match(entry):
            name = await graph.get_group_name_by_id(entry)
            return {"input": entry, "team_id": entry, "name": name, "found": name is not None}
        else:
            team_id = await graph.search_group_by_name(entry)
            name = await graph.get_group_name_by_id(team_id) if team_id else None
            return {"input": entry, "team_id": team_id, "name": name or entry, "found": team_id is not None}

    results = await asyncio.gather(*(resolve_one(e) for e in req.entries))
    return [r for r in results if r is not None]


class BulkDeleteTeamsRequest(BaseModel):
    team_ids: list[str]


@router.post("/bulk-delete", summary="Eliminación masiva de Teams por ID")
async def bulk_delete_teams(req: BulkDeleteTeamsRequest):
    """Toma una lista de IDs de grupo/Team (ya resueltos vía /resolve) y los elimina en lote."""
    result = {"succeeded": [], "failed": []}

    async def delete_one(team_id: str):
        name = await graph.get_group_name_by_id(team_id) or team_id
        try:
            await graph.delete(f"/groups/{team_id}")
            result["succeeded"].append({"team_id": team_id, "name": name})
        except Exception as e:
            result["failed"].append({"team_id": team_id, "name": name, "error": str(e)})

    for tid in req.team_ids:
        await delete_one(tid)

    return result


# ── Members ───────────────────────────────────────────────────────────────────

@router.get("/{team_id}/members", summary="Listar miembros del Team")
async def list_members(team_id: str):
    return await graph.paginate(f"/teams/{team_id}/members")




@router.post("/{team_id}/members/bulk-add", summary="Añadir miembros de forma conjunta")
async def bulk_add_members(team_id: str, body: BulkTeamsMemberAdd) -> BulkResult:
    # Graph supports up to 20 members per batch via addMembers action
    result = BulkResult()
    BATCH_SIZE = 20

    members_payload = [
        {
            "@odata.type": "#microsoft.graph.aadUserConversationMember",
            "roles": [m.role] if m.role == "owner" else [],
            "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{m.user_id}')",
        }
        for m in body.members
    ]

    for i in range(0, len(members_payload), BATCH_SIZE):
        batch = members_payload[i : i + BATCH_SIZE]
        try:
            resp = await graph.post(f"/teams/{team_id}/members/add", {"values": batch})
            added = resp.get("value", [])
            errors = resp.get("error", [])
            result.succeeded.extend(added)
            result.failed.extend(errors)
        except Exception as exc:
            for m in body.members[i : i + BATCH_SIZE]:
                result.failed.append({"user_id": m.user_id, "error": str(exc)})

    return result


@router.post("/{team_id}/members/bulk-add-emails", summary="Añadir miembros por lista de correos")
async def bulk_add_members_by_email(team_id: str, body: BulkTeamsEmailAdd) -> BulkResult:
    result = BulkResult()
    BATCH_SIZE = 20

    # 1. Lookup emails in Azure AD to get Object IDs
    user_ids = []
    
    async def _lookup(email: str):
        try:
            # First try userPrincipalName or mail directly
            # Often mailNickname is also supported, but upn is safer
            user = await graph.get(f"/users/{email.strip()}", params={"$select": "id,mail,userPrincipalName"})
            user_ids.append({"email": email, "id": user["id"]})
        except Exception as exc:
            # If not found by direct ID/UPN, try searching by mail
            try:
                search_res = await graph.get("/users", params={"$filter": f"mail eq '{email.strip()}'", "$select": "id"})
                if search_res.get("value") and len(search_res["value"]) > 0:
                    user_ids.append({"email": email, "id": search_res["value"][0]["id"]})
                else:
                    result.failed.append({"input": email, "error": "Usuario no encontrado en Azure AD"})
            except Exception as e:
                result.failed.append({"input": email, "error": "Usuario no encontrado en Azure AD"})

    # Run lookups concurrently
    await asyncio.gather(*[_lookup(email) for email in set(body.emails) if email.strip()])

    if not user_ids:
        return result

    # 2. Add them in batches
    members_payload = [
        {
            "@odata.type": "#microsoft.graph.aadUserConversationMember",
            "roles": [body.role] if body.role == "owner" else [],
            "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{u['id']}')",
        }
        for u in user_ids
    ]

    for i in range(0, len(members_payload), BATCH_SIZE):
        batch = members_payload[i : i + BATCH_SIZE]
        try:
            resp = await graph.post(f"/teams/{team_id}/members/add", {"values": batch})
            added = resp.get("value", [])
            errors = resp.get("error", [])
            
            # Map back to email if possible for better frontend reporting
            for success in added:
                result.succeeded.append(success)
            for err in errors:
                result.failed.append({"input": "Lote", "error": str(err)})
        except Exception as exc:
            for u in user_ids[i : i + BATCH_SIZE]:
                result.failed.append({"input": u["email"], "error": str(exc)})

    return result


@router.delete("/{team_id}/members/{membership_id}", summary="Quitar miembro del Team")
async def remove_member(team_id: str, membership_id: str):
    try:
        await graph.delete(f"/teams/{team_id}/members/{membership_id}")
        return {"removed": membership_id}
    except StarletteHTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{team_id}/members/bulk-remove", summary="Quitar miembros de forma conjunta")
async def bulk_remove_members(team_id: str, body: BulkTeamsMemberRemove) -> BulkResult:
    result = BulkResult()

    # Retrieve current members to map user_id → membership_id
    try:
        members = await graph.paginate(f"/teams/{team_id}/members")
    except StarletteHTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    id_to_membership = {m.get("userId"): m.get("id") for m in members}

    async def _remove(user_id: str):
        membership_id = id_to_membership.get(user_id)
        if not membership_id:
            result.failed.append({"user_id": user_id, "error": "Member not found in team"})
            return
        try:
            await graph.delete(f"/teams/{team_id}/members/{membership_id}")
            result.succeeded.append({"user_id": user_id, "removed": True})
        except Exception as exc:
            result.failed.append({"user_id": user_id, "error": str(exc)})

    await asyncio.gather(*[_remove(uid) for uid in body.user_ids])
    return result


# ── Channels ─────────────────────────────────────────────────────────────────

@router.get("/{team_id}/channels", summary="Listar canales del Team")
async def list_channels(team_id: str):
    return await graph.paginate(f"/teams/{team_id}/channels")


@router.post("/{team_id}/channels", status_code=201, summary="Crear canal en el Team")
async def create_channel(team_id: str, body: TeamsChannelCreate):
    payload = {
        "displayName": body.display_name,
        "description": body.description or "",
        "membershipType": body.membership_type,
    }
    try:
        return await graph.post(f"/teams/{team_id}/channels", payload)
    except StarletteHTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

