code_to_add = """
@router.post("/excel/docentes-onedrive/preview", summary="Previsualizar Docentes desde OneDrive")
async def preview_docentes_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL invlida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar de OneDrive. {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo no es un Excel vlido.")

    if req.sheet_name not in wb.sheetnames:
        raise HTTPException(status_code=400, detail=f"La pestaa '{req.sheet_name}' no existe.")

    ws = wb[req.sheet_name]
    
    header_row_idx = None
    headers = {}
    for row_idx in range(1, min(6, ws.max_row + 1)):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip().lower() for c in range(1, ws.max_column + 1)]
        if any("nombre" in v for v in row_vals) and any("cedula" in v or "cdula" in v or "ci" in v for v in row_vals):
            header_row_idx = row_idx
            for col_idx, val in enumerate(row_vals, 1):
                headers[_norm(val)] = col_idx
            break
            
    if not header_row_idx:
        raise HTTPException(status_code=400, detail="No se encontraron las columnas de 'Nombre' y 'Cdula'.")

    def get_col_idx(*keys):
        for k in keys:
            for h, idx in headers.items():
                if _norm(k) in h:
                    return idx
        return None

    col_nombre = get_col_idx("nombre")
    col_cedula = get_col_idx("cedula", "cdula", "ci")
    col_correo = get_col_idx("correo", "email")
    col_plat = get_col_idx("plataforma")
    col_curso = get_col_idx("curso", "id curso", "canvas")
    col_equipo = get_col_idx("equipo", "id equipo", "teams")
    col_enviado = get_col_idx("enviado", "estado")

    rows = []
    for r_idx in range(header_row_idx + 1, ws.max_row + 1):
        nombre = str(ws.cell(row=r_idx, column=col_nombre).value or "").strip()
        cedula = str(ws.cell(row=r_idx, column=col_cedula).value or "").strip()
        
        if not nombre or not cedula or cedula == "None":
            continue
            
        correo = str(ws.cell(row=r_idx, column=col_correo).value or "").strip() if col_correo else ""
        plat = str(ws.cell(row=r_idx, column=col_plat).value or "both").strip().lower() if col_plat else "both"
        id_curso = str(ws.cell(row=r_idx, column=col_curso).value or "").strip() if col_curso else ""
        id_equipo = str(ws.cell(row=r_idx, column=col_equipo).value or "").strip() if col_equipo else ""
        
        if col_enviado:
            enviado = str(ws.cell(row=r_idx, column=col_enviado).value or "").strip()
            if "?" in enviado or enviado.lower() in ["si", "yes", "true", "enviado"]:
                continue

        rows.append({
            "nombre": nombre,
            "cedula": cedula,
            "correo": correo,
            "plataforma": plat,
            "curso": id_curso,
            "equipo": id_equipo
        })
        if len(rows) >= 10:
            break

    return PreviewResponse(
        total_rows=ws.max_row - header_row_idx,
        valid_rows=len(rows),
        sample=rows
    )

@router.post("/excel/docentes-onedrive", summary="Alta Docentes OneDrive")
async def import_docentes_onedrive(req: DiplomadosUrlRequest, background_tasks: BackgroundTasks, auth: dict = Depends(require_auth)) -> BulkResult:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL invlida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo de OneDrive. {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo descargado no es un Excel vlido.")

    _ACCOUNT_LOCAL = settings.canvas_account_id
    result = BulkResult()

    if req.sheet_name not in wb.sheetnames:
        raise HTTPException(status_code=400, detail=f"La pestaa '{req.sheet_name}' no existe.")

    ws = wb[req.sheet_name]
    
    header_row_idx = None
    headers = {}
    for row_idx in range(1, min(6, ws.max_row + 1)):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip().lower() for c in range(1, ws.max_column + 1)]
        if any("nombre" in v for v in row_vals) and any("cedula" in v or "cdula" in v or "ci" in v for v in row_vals):
            header_row_idx = row_idx
            for col_idx, val in enumerate(row_vals, 1):
                headers[_norm(val)] = col_idx
            break
    
    if not header_row_idx:
        raise HTTPException(status_code=400, detail="Columnas de Nombre y Cdula no encontradas.")

    def get_col_idx(*keys):
        for k in keys:
            for h, idx in headers.items():
                if _norm(k) in h:
                    return idx
        return None

    col_nombre = get_col_idx("nombre")
    col_cedula = get_col_idx("cedula", "cdula", "ci")
    col_correo = get_col_idx("correo", "email")
    col_plat = get_col_idx("plataforma")
    col_curso = get_col_idx("curso", "id curso", "canvas")
    col_equipo = get_col_idx("equipo", "id equipo", "teams")
    
    col_usuario = get_col_idx("usuario")
    col_contra = get_col_idx("contrasena", "contrasea", "clave")
    col_enviado = get_col_idx("enviado", "estado")

    next_col = ws.max_column + 1
    if not col_usuario:
        col_usuario = next_col; ws.cell(row=header_row_idx, column=col_usuario, value="Usuario").font = Font(bold=True); next_col += 1
    if not col_contra:
        col_contra = next_col; ws.cell(row=header_row_idx, column=col_contra, value="Contrasea").font = Font(bold=True); next_col += 1
    if not col_enviado:
        col_enviado = next_col; ws.cell(row=header_row_idx, column=col_enviado, value="Estado").font = Font(bold=True); next_col += 1

    users_to_process = []
    for r_idx in range(header_row_idx + 1, ws.max_row + 1):
        nombre = str(ws.cell(row=r_idx, column=col_nombre).value or "").strip()
        cedula = str(ws.cell(row=r_idx, column=col_cedula).value or "").strip()
        
        if not nombre or not cedula or cedula == "None":
            continue
            
        enviado = str(ws.cell(row=r_idx, column=col_enviado).value or "").strip()
        if "?" in enviado or enviado.lower() in ["si", "yes", "true", "enviado", "ok"]:
            continue
            
        users_to_process.append(r_idx)

    for r_idx in users_to_process:
        nombre = str(ws.cell(row=r_idx, column=col_nombre).value or "").strip()
        cedula = str(ws.cell(row=r_idx, column=col_cedula).value or "").strip()
        correo = str(ws.cell(row=r_idx, column=col_correo).value or "").strip() if col_correo else ""
        plat = str(ws.cell(row=r_idx, column=col_plat).value or "both").strip().lower() if col_plat else "both"
        id_curso = str(ws.cell(row=r_idx, column=col_curso).value or "").strip() if col_curso else ""
        id_equipo = str(ws.cell(row=r_idx, column=col_equipo).value or "").strip() if col_equipo else ""

        creds = generate_credentials(nombre, cedula, settings.institutional_domain)
        login_id = creds["email"]
        pwd = creds["password"]
        
        entry = {"cedula": cedula, "nombre": creds["full_name"], "login_id": login_id}
        error = ""
        
        # Azure AD
        azure_id = None
        if plat in ("teams", "both"):
            parts = creds["full_name"].strip().split()
            try:
                au = await graph.post("/users", {
                    "displayName": creds["full_name"],
                    "givenName": parts[0],
                    "surname": " ".join(parts[1:]) if len(parts) > 1 else "",
                    "userPrincipalName": login_id,
                    "mailNickname": login_id.replace(".", "_").replace("@", "_"),
                    "usageLocation": settings.usage_location,
                    "accountEnabled": True,
                    "passwordProfile": {
                        "forceChangePasswordNextSignIn": True,
                        "password": pwd,
                    },
                })
                azure_id = au["id"]
                await graph.assign_license(azure_id, settings.azure_sku_teachers)
                entry["teams"] = "creado"
            except Exception as e:
                if "already exists" in str(e).lower() or "Request_BadRequest" in str(e):
                    # Try to fetch existing
                    try:
                        ex_users = await graph.search_users(login_id)
                        if ex_users:
                            azure_id = ex_users[0]["id"]
                            entry["teams"] = "exista"
                    except:
                        pass
                else:
                    error += f"Teams: {str(e)} | "

        # Azure Teams Enrollment
        if id_equipo and azure_id and id_equipo != "None":
            try:
                await graph.post(f"/groups/{id_equipo}/owners/$ref", {
                    "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{azure_id}"
                })
                entry["teams_enroll"] = "owner"
            except Exception as e:
                if "already" not in str(e).lower():
                    error += f"TeamsEnroll: {str(e)} | "

        # Canvas
        canvas_id = None
        if plat in ("canvas", "both"):
            try:
                cu = await canvas_client.post(f"/accounts/{_ACCOUNT_LOCAL}/users", {
                    "user": {
                        "name": creds["full_name"],
                        "sortable_name": creds["full_name"],
                        "short_name": parts[0] + " " + parts[-1] if len(parts)>1 else creds["full_name"]
                    },
                    "pseudonym": {
                        "unique_id": login_id,
                        "sis_user_id": cedula,
                        "password": pwd,
                        "send_confirmation": False
                    },
                    "communication_channel": {
                        "type": "email", "address": login_id,
                        "skip_confirmation": True,
                    },
                })
                canvas_id = cu["id"]
                entry["canvas"] = "creado"
            except Exception as e:
                try:
                    ex_c = await canvas_client.get(f"/accounts/{_ACCOUNT_LOCAL}/users", params={"search_term": login_id})
                    if ex_c:
                        canvas_id = ex_c[0]["id"]
                        entry["canvas"] = "exista"
                except:
                    pass
                if not canvas_id:
                    error += f"Canvas: {str(e)} | "

        # Canvas Enrollment
        if id_curso and canvas_id and id_curso != "None":
            try:
                await canvas_client.post(f"/courses/{id_curso}/enrollments", {
                    "enrollment": {
                        "user_id": canvas_id,
                        "type": "TeacherEnrollment",
                        "enrollment_state": "active",
                        "notify": False
                    }
                })
                entry["canvas_enroll"] = "teacher"
            except Exception as e:
                error += f"CanvasEnroll: {str(e)} | "
                
        if error:
            ws.cell(row=r_idx, column=col_enviado, value=f"?O Error: {error}")
            ws.cell(row=r_idx, column=col_enviado).font = Font(color="D97706", bold=True)
            result.failed.append({"correo": login_id, "error": error})
        else:
            ws.cell(row=r_idx, column=col_usuario, value=login_id)
            ws.cell(row=r_idx, column=col_contra, value=pwd)
            ws.cell(row=r_idx, column=col_enviado, value="? OK")
            ws.cell(row=r_idx, column=col_enviado).font = Font(color="00B050", bold=True)
            result.succeeded.append(entry)

    if len(users_to_process) > 0:
        out_io = io.BytesIO()
        wb.save(out_io)
        out_io.seek(0)
        try:
            await graph.put_raw(f"/shares/{encoded_url}/driveItem/content", out_io.read())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"No se pudo guardar el archivo actualizado en OneDrive. {e}")

    background_tasks.add_task(
        add_job_history,
        user=auth.get("name", "Unknown"),
        job_type="Alta Docentes (OneDrive)",
        details=f"Pestaa: {req.sheet_name}",
        status="Completado" if not result.failed else "Con Errores",
        success_count=len(result.succeeded),
        error_count=len(result.failed),
        error_details="; ".join([f"{f['correo']}: {f['error']}" for f in result.failed]) if result.failed else None
    )

    return result
"""

with open(r"Backend\app\routers\excel.py", "a", encoding="utf-8") as f:
    f.write("\n" + code_to_add + "\n")
