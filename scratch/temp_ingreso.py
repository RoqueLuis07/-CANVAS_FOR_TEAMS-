async def preview_students_bulk(body: BulkStudentsIn) -> dict:
    """Simula la creación de múltiples usuarios y retorna qué credenciales y estados tendrían."""
    sample = []
    
    async def _preview(student: StudentIn):
        creds, status = await user_service.generate_unique_credentials(
            student.full_name, student.cedula, platform=student.platform
        )
        login_id, sis_user_id = _resolve_login(creds, student.role)
        
        status_canvas = "-"
        status_teams = "-"
        
        if student.platform in ("canvas", "both"):
            exists, _ = await user_service._canvas_user_exists(sis_user_id, login_id)
            status_canvas = "exists" if exists else "new"
            
        if student.platform in ("teams", "both"):
            exists, _ = await user_service._teams_user_exists(creds["email"])
            status_teams = "exists" if exists else "new"
            
        sample.append({
            "nombre": student.full_name,
            "cedula": student.cedula,
            "correo_personal": student.personal_email,
            "login_id": login_id,
            "correo_institucional": creds["email"],
            "password": creds["password"],
            "plataforma": student.platform,
            "status_canvas": status_canvas,
            "status_teams": status_teams
        })

    import asyncio
    await asyncio.gather(*[_preview(s) for s in body.students])
    
    return {
        "total_rows": len(body.students),
        "valid_rows": len(body.students),
        "sample": sample
