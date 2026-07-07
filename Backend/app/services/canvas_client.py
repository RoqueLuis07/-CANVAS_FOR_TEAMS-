"""HTTP client wrapper for the Canvas LMS REST API v1."""
import asyncio
from typing import Any

import httpx
from fastapi import HTTPException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings

_BASE = f"{settings.canvas_base_url.rstrip('/')}/api/v1"
_HEADERS = {"Authorization": f"Bearer {settings.canvas_access_token}"}
_TIMEOUT = httpx.Timeout(30.0)

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

# Retry transient network errors and HTTP 429 (Too Many Requests) / 5xx errors.
_TRANSIENT = (
    httpx.ConnectError,
    httpx.TimeoutException,
    httpx.RemoteProtocolError,
    httpx.ReadError,
)

def _should_retry(e: Exception) -> bool:
    if isinstance(e, _TRANSIENT):
        return True
    if isinstance(e, HTTPException) and e.status_code in (429, 502, 503, 504):
        return True
    return False

_retry = retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(5),
    wait=wait_exponential(min=1, max=16),
    reraise=True,
)


_client_instance: httpx.AsyncClient | None = None

def _client() -> httpx.AsyncClient:
    global _client_instance
    if _client_instance is None or _client_instance.is_closed:
        _client_instance = httpx.AsyncClient(base_url=_BASE, headers=_HEADERS, timeout=_TIMEOUT)
    return _client_instance

async def close_client() -> None:
    global _client_instance
    if _client_instance is not None and not _client_instance.is_closed:
        await _client_instance.aclose()
        _client_instance = None


def _raise(r: httpx.Response) -> None:
    if r.is_error:
        try:
            import json as _json
            body = _json.loads(r.content.decode("utf-8", errors="replace"))
            if isinstance(body, dict):
                errors = body.get("errors") or body.get("message") or body
            else:
                errors = body
        except Exception:
            errors = r.text or r.reason_phrase

        msg = f"Canvas API {r.status_code}"

        if r.status_code == 401:
            msg = "Canvas API: token inválido o expirado (401). Generá un nuevo token en Canvas → Configuración → Tokens de acceso."
        elif r.status_code == 403:
            msg = "Canvas API: acceso denegado (403). El token no tiene permisos de administrador sobre esta cuenta."
        elif isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                msg = f"Canvas API {r.status_code}: {first.get('message') or first.get('type') or str(first)}"
        elif isinstance(errors, str) and errors:
            msg = f"Canvas API {r.status_code}: {errors[:300]}"
        elif isinstance(errors, dict):
            # Canvas nested format: {"field": {"subfield": [{"type": "...", "message": "..."}]}}
            parts = []
            for field, field_errors in errors.items():
                if isinstance(field_errors, list):
                    for e in field_errors:
                        parts.append(f"{field}: {e.get('message', e.get('type', str(e)))}")
                elif isinstance(field_errors, dict):
                    for subfield, sub_errors in field_errors.items():
                        if isinstance(sub_errors, list):
                            for e in sub_errors:
                                parts.append(f"{field}.{subfield}: {e.get('message', e.get('type', str(e)))}")
            if parts:
                msg = f"Canvas API {r.status_code}: {' | '.join(parts)}"

        raise HTTPException(status_code=r.status_code, detail=msg)


@_retry
async def get(path: str, params: dict | None = None) -> Any:
    r = await _client().get(path, params=params)
    _raise(r)
    return r.json()


@_retry
async def post(path: str, payload: dict) -> Any:
    r = await _client().post(path, json=payload)
    _raise(r)
    return r.json()


@_retry
async def put(path: str, payload: dict) -> Any:
    r = await _client().put(path, json=payload)
    _raise(r)
    return r.json()


@_retry
async def delete(path: str, params: dict | None = None) -> Any:
    r = await _client().delete(path, params=params)
    _raise(r)
    return r.json() if r.content else {}


async def paginate(path: str, params: dict | None = None) -> list[Any]:
    """Follow Canvas Link-header pagination and return all records."""
    results: list[Any] = []
    params = dict(params or {})
    params.setdefault("per_page", 100)
    next_url: str | None = path

    c = _client()
    while next_url:
        if next_url.startswith("http"):
            r = await c.get(next_url, params=params if next_url == path else None)
        else:
            r = await c.get(next_url, params=params)
        _raise(r)
        data = r.json()
        if isinstance(data, list):
            results.extend(data)
        else:
            results.append(data)
        link = r.headers.get("Link", "")
        next_url = _parse_next_link(link)

    return results


async def paginate_limited(path: str, params: dict | None = None,
                           max_records: int = 1000) -> list[Any]:
    """Paginate following Link headers but stop at max_records.

    Used for list endpoints in the web UI where loading unlimited records
    could cause timeouts. Returns up to max_records sorted by the API order.
    """
    results: list[Any] = []
    params = dict(params or {})
    params.setdefault("per_page", 100)
    next_url: str | None = path

    c = _client()
    while next_url and len(results) < max_records:
        if next_url.startswith("http"):
            r = await c.get(next_url, params=params if next_url == path else None)
        else:
            r = await c.get(next_url, params=params)
        _raise(r)
        data = r.json()
        if isinstance(data, list):
            results.extend(data)
        else:
            results.append(data)
        link = r.headers.get("Link", "")
        next_url = _parse_next_link(link)

    return results[:max_records]


def _parse_next_link(link_header: str) -> str | None:
    for part in link_header.split(","):
        segments = part.strip().split(";")
        if len(segments) == 2 and 'rel="next"' in segments[1]:
            return segments[0].strip().strip("<>")
    return None


async def search_course_by_name(account_id: str, course_name: str) -> str | None:
    """Search for a Canvas course by name in the given account. Returns course ID if found."""
    try:
        results = await get(f"/accounts/{account_id}/courses", params={"search_term": course_name, "include[]": "total_students"})
        if results and isinstance(results, list):
            for c in results:
                if c.get("name") == course_name:
                    return str(c.get("id"))
    except Exception:
        pass
    return None

async def create_course(account_id: str, course_name: str) -> str | None:
    """Create a Canvas course in the given account."""
    try:
        res = await post(f"/accounts/{account_id}/courses", {
            "course": {
                "name": course_name,
                "course_code": course_name[:15],
                "enrollment_term_id": 1,
                "workflow_state": "available"
            }
        })
        if res and "id" in res:
            return str(res["id"])
    except Exception:
        pass
    return None

async def get_course_name_by_id(course_id: str) -> str | None:
    """Get Canvas course name by ID."""
    try:
        res = await get(f"/courses/{course_id}")
        if res and "name" in res:
            return res["name"]
    except Exception:
        pass
    return None
