def import_matriculaciones_onedrive(req: DiplomadosUrlRequest) -> BulkResult:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error descargando archivo de OneDrive: {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo no es un Excel válido.")

    result = BulkResult()
    if req.sheet_name not in wb.sheetnames:
        raise HTTPException(status_code=400, detail=f"La pestaña '{req.sheet_name}' no existe.")

    ws = wb[req.sheet_name]
    headers = {c.value: c.column for c in ws[1] if c.value}
    
    # Identify columns
    user_col, canvas_col, teams_col, rol_col, env_col = None, None, None, None, None
    for h, col_idx in headers.items():
        n = _norm(h)
        if "usuario" in n or "correo" in n or "email" in n or "cedula" in n:
            user_col = col_idx
        elif "curso" in n or "canvas" in n:
            canvas_col = col_idx
        elif "equipo" in n or "teams" in n:
            teams_col = col_idx
        elif "rol" in n:
            rol_col = col_idx
        elif "enviado" in n or "estado" in n:
            env_col = col_idx

    if not user_col or not (canvas_col or teams_col):
        raise HTTPException(status_code=400, detail="El archivo debe tener al menos una columna de 'usuario' y una de 'curso/canvas' o 'equipo/teams'.")
    if not env_col:
        env_col = ws.max_column + 1
        ws.cell(row=1, column=env_col, value="Enviado")

    # Import dependencies specifically inside function to avoid circular imports or missing vars
    from app.routers.sync import _enroll_single
    from app.models.sync import UnifiedEnrollment

    tasks = []
    
    async def process_row(r_idx):
        user_val = str(ws.cell(row=r_idx, column=user_col).value or "").strip()
        if not user_val:
            return None
        
        canvas_val = str(ws.cell(row=r_idx, column=canvas_col).value or "").strip() if canvas_col else ""
        teams_val = str(ws.cell(row=r_idx, column=teams_col).value or "").strip() if teams_col else ""
        rol_val = str(ws.cell(row=r_idx, column=rol_col).value or "estudiante").strip().lower() if rol_col else "estudiante"
        
        # Mapear rol
        mapped_role = "teacher" if "prof" in rol_val or "own" in rol_val or "propiet" in rol_val else "student"

        enroll_item = UnifiedEnrollment(
            user_identifier=user_val,
            canvas_course_id=canvas_val,
            teams_team_id=teams_val,
            role=mapped_role
        )
        
        try:
            enroll_res = await _enroll_single(enroll_item)
            if enroll_res.get("status") == "success":
                result.succeeded.append({"correo": user_val, "mensaje": "Matriculado"})
                ws.cell(row=r_idx, column=env_col, value="OK").fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            else:
                msg = enroll_res.get("message", "Error desconocido")
                result.failed.append({"correo": user_val, "error": msg})
                ws.cell(row=r_idx, column=env_col, value=f"Error: {msg}").fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        except Exception as ex:
            msg = str(ex)
            result.failed.append({"correo": user_val, "error": msg})
            ws.cell(row=r_idx, column=env_col, value=f"Error: {msg}").fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for r_idx in range(2, ws.max_row + 1):
        tasks.append(process_row(r_idx))
    
    # Process tasks in chunks to avoid rate limiting
    batch_size = 5
    for i in range(0, len(tasks), batch_size):
        await asyncio.gather(*(t for t in tasks[i:i+batch_size] if t is not None))

    # Save to OneDrive
    out_io = io.BytesIO()
    wb.save(out_io)
    out_io.seek(0)
    
    try:
        await graph.put_raw(f"/shares/{encoded_url}/driveItem/content", out_io.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar en OneDrive: {e}")

    return result