from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import uuid
from datetime import datetime

from app.services import canvas_client as canvas
from app.services import teams_client as teams

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
                # Graph API uses user email/UPN directly
                await teams.add_member(materia.teams_group_id, req.email, "member")
                teams_status = "OK"
            except Exception as e:
                teams_status = f"Error: {str(e)}"
                
        results.append({
            "materia_id": materia.id,
            "materia_name": materia.name,
            "canvas_status": canvas_status,
            "teams_status": teams_status
        })
        
    # Log History
    log_history(req, results)
    
    return {"status": "success", "results": results}

def log_history(req, results):
    log_file = os.path.join(os.path.dirname(__file__), "..", "data", "matriculaciones_history.json")
    history = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
                
    history.append({
        "timestamp": datetime.now().isoformat(),
        "email": req.email,
        "sys_id": req.sys_id,
        "program": req.program,
        "platforms": req.platforms,
        "results": results
    })
    
    # Keep only the last 100 entries to prevent huge file
    history = history[-100:]
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

@router.get("/api/matriculacion/history")
async def get_history():
    log_file = os.path.join(os.path.dirname(__file__), "..", "data", "matriculaciones_history.json")
    if not os.path.exists(log_file):
        return []
    with open(log_file, "r", encoding="utf-8") as f:
        try:
            history = json.load(f)
            # Return sorted by timestamp descending
            return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
        except json.JSONDecodeError:
            return []
