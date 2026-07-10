import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.egreso.canvas.get", new_callable=AsyncMock)
@patch("app.routers.egreso.canvas.delete", new_callable=AsyncMock)
@patch("app.routers.egreso.graph.get", new_callable=AsyncMock)
@patch("app.routers.egreso.graph.patch", new_callable=AsyncMock)
def test_egreso_suspend_canvas_not_found_teams_found(mock_graph_patch, mock_graph_get, mock_canvas_delete, mock_canvas_get):
    # Simulamos que Canvas tira 404
    mock_canvas_get.side_effect = Exception("404 Not Found")
    
    # Simulamos que Teams sí encuentra el usuario por el email provisto
    mock_graph_get.return_value = {"value": [{"id": "teams-id-123"}]}
    
    response = client.post("/egreso/suspend?sys_user_id=123&email=test@usil.edu.py")
    
    assert response.status_code == 200
    data = response.json()
    assert data["canvas"] == "not_found"
    assert data["teams"] == "suspended"
    
    mock_graph_get.assert_called_once_with("/users", params={"$filter": "userPrincipalName eq 'test@usil.edu.py'"})
    mock_graph_patch.assert_called_once_with("/users/teams-id-123", {"accountEnabled": False})


@patch("app.routers.matriculacion.canvas.get", new_callable=AsyncMock)
@patch("app.routers.matriculacion.canvas.post", new_callable=AsyncMock)
@patch("app.routers.matriculacion.teams.search_users", new_callable=AsyncMock)
@patch("app.routers.matriculacion.teams.add_member_to_group", new_callable=AsyncMock)
@patch("app.routers.matriculacion.jobs.create_job", new_callable=AsyncMock)
@patch("app.routers.matriculacion.jobs.start_job", new_callable=AsyncMock)
@patch("app.routers.matriculacion.jobs.complete_job", new_callable=AsyncMock)
def test_matriculacion_individual(mock_complete_job, mock_start_job, mock_create_job, 
                                  mock_teams_add, mock_teams_search, 
                                  mock_canvas_post, mock_canvas_get):
    
    mock_canvas_get.return_value = [{"id": "canvas-user-123"}]
    mock_teams_search.return_value = [{"id": "teams-user-123"}]
    mock_create_job.return_value = 999
    
    payload = {
        "email": "student@usil.edu.py",
        "sys_id": "456",
        "program": "grado",
        "materias": [
            {
                "id": "MAT101",
                "name": "Matematica 1",
                "program": "grado",
                "canvas_course_id": "1001",
                "teams_group_id": "group-1001"
            }
        ],
        "platforms": "both"
    }
    
    response = client.post("/api/matriculacion/individual", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["results"][0]["canvas_status"] == "OK"
    assert data["results"][0]["teams_status"] == "OK"
    
    mock_create_job.assert_called_once()
    mock_start_job.assert_called_once_with(999)
    mock_complete_job.assert_called_once_with(job_id=999, result_count=1, error_count=0)
