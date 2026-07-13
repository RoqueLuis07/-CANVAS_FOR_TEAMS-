from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import json
import os

from app.services import canvas_client as canvas
from app.services import teams_client as teams
from app.core import jobs

router = APIRouter(tags=["Matriculaciones Individuales"])

# Models
class MateriaSearchRequest(BaseModel):
    program: str
    q: Optional[str] = ""

class MateriaResponse(BaseModel):
    id: str
    name: str
    program: str
    canvas_course_id: Optional[str]
    teams_group_id: Optional[str]

class IndividualEnrollmentRequest(BaseModel):
    email: str
    sys_id: str
    program: str
    materias: List[MateriaResponse]
    platforms: str # "canvas", "teams", or "both"

class EnrollmentResult(BaseModel):
    materia_id: str
    materia_name: str
    canvas_status: str
    teams_status: str

# Helper to load catalogue
def load_catalogue():
    catalogue_path = os.path.join(os.path.dirname(__file__), "..", "data", "catalogo_materias.json")
    if not os.path.exists(catalogue_path):
        return []
    with open(catalogue_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

@router.get("/api/matriculacion/materias", response_model=List[MateriaResponse])
async def search_materias(program: str, q: str = "",):
    catalogue = load_catalogue()
    
    # Filter by program
    filtered = [m for m in catalogue if m.get("program", "").lower() == program.lower()]
    
    # Filter by search query (id or name)
    if q:
        q_lower = q.lower()
        filtered = [m for m in filtered if q_lower in m.get("name", "").lower() or q_lower in m.get("id", "").lower()]
        
    return filtered

@router.post("/api/matriculacion/individual")
async def matriculate_individual(req: IndividualEnrollmentRequest,):
    results = []
    
    # Look up the user in canvas to get canvas user ID if needed
    canvas_user_id = None
    if req.platforms in ["canvas", "both"]:
        # Try to find by SIS ID first
        try:
            res = await canvas.get(f"/accounts/1/users?search_term={req.sys_id}")
            if res and len(res) > 0:
                canvas_user_id = res[0]["id"]
            else:
                # Try by email
                res = await canvas.get(f"/accounts/1/users?search_term={req.email}")
                if res and len(res) > 0:
                    canvas_user_id = res[0]["id"]
        except Exception as e:
            print(f"Error finding canvas user: {e}")

    for materia in req.materias:
        canvas_status = "Skipped"
        teams_status = "Skipped"
        
        # Canvas Enrollment
        if req.platforms in ["canvas", "both"] and materia.canvas_course_id:
            if not canvas_user_id:
                canvas_status = "Error: Usuario no encontrado en Canvas"
            else:
                try:
                    payload = {
                        "enrollment": {
                            "user_id": canvas_user_id,
                            "type": "StudentEnrollment",
                            "enrollment_state": "active",
                            "notify": False
                        }
                    }
                    # Need to figure out the right canvas course identifier. Assumed it's the id directly.
                    # Usually course ID in canvas is an integer. Let's try raw id or sis_course_id.
                    course_ref = materia.canvas_course_id
                    # We will use raw id if it's numeric, otherwise sis_course_id
                    endpoint = f"/courses/{course_ref}/enrollments"
                    if not str(course_ref).isdigit():
                        endpoint = f"/courses/sis_course_id:{course_ref}/enrollments"
                        
                    await canvas.post(endpoint, payload)
                    canvas_status = "OK"
                except Exception as e:
                    canvas_status = f"Error: {str(e)}"
                    
        # Teams Enrollment
        if req.platforms in ["teams", "both"] and materia.teams_group_id:
            try:
                azure_user = await teams.search_users(req.email)
                if azure_user:
                    uid = azure_user[0]["id"]
                    await teams.add_member_to_group(materia.teams_group_id, uid)
                    teams_status = "OK"
                else:
                    teams_status = "Error: Usuario no encontrado en Teams"
            except Exception as e:
                teams_status = f"Error: {str(e)}"
                
        results.append({
            "materia_id": materia.id,
            "materia_name": materia.name,
            "canvas_status": canvas_status,
            "teams_status": teams_status
        })
        
    # Log History in SQLite Jobs
    error_count = sum(1 for r in results if 'Error' in r['canvas_status'] or 'Error' in r['teams_status'])
    job_id = await jobs.create_job(
        job_type="matriculacion_individual",
        operation="matriculacion",
        username="sistema",
        details=f"Matriculación de {req.email}",
        data_json=json.dumps({"req": req.dict(), "results": results})
    )
    if job_id:
        await jobs.start_job(job_id)
        await jobs.complete_job(
            job_id=job_id,
            result_count=len(results),
            error_count=error_count
        )
    
    return {"status": "success", "results": results}

@router.get("/api/matriculacion/history")
async def get_history():
    result = await jobs.get_jobs(job_type="matriculacion_individual", limit=100)
    history = []
    for job in result.get("jobs", []):
        try:
            data = json.loads(job["data_json"]) if job.get("data_json") else {}
            req_data = data.get("req", {})
            
            created_at = job["created_at"]
            if hasattr(created_at, "isoformat"):
                timestamp = created_at.isoformat()
            else:
                timestamp = str(created_at)
                
            history.append({
                "timestamp": timestamp,
                "email": req_data.get("email", ""),
                "sys_id": req_data.get("sys_id", ""),
                "program": req_data.get("program", ""),
                "platforms": req_data.get("platforms", ""),
                "results": data.get("results", [])
            })
        except Exception as e:
            print(f"Error parsing job history: {e}")
            
    return history
