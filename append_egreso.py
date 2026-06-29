import sys

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_code = '''
# ------------------------------------------------------------------
# Egreso Masivo (Offboarding) con OneDrive y Graph API
# ------------------------------------------------------------------

@router.post("/excel/egreso/preview", response_model=PreviewResponse)
async def preview_egreso_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        range_data = await graph.get(f"/shares/{encoded_url}/driveItem/workbook/worksheets('{req.sheet_name}')/usedRange")
    except Exception as e:
        if "ItemNotFound" in str(e):
            raise HTTPException(status_code=400, detail=f"La pestaña '{req.sheet_name}' no existe o el archivo no es un Excel válido.")
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo de Excel. {e}")

    values = range_data.get("values", [])
    if not values:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    header_r_idx = None
    headers = {}
    
    # Buscamos en las primeras 6 filas
    for r_idx, row in enumerate(values[:6]):
        row_vals = [str(v or "").strip().lower() for v in row]
        if any("cedula" in v or "cédula" in v or "ci" in v for v in row_vals):
            header_r_idx = r_idx
            for c_idx, val in enumerate(row_vals):
                if val:
                    headers[_norm(val)] = c_idx
            break
            
    if header_r_idx is None:
        raise HTTPException(status_code=400, detail="No se encontró la columna 'Cédula' o equivalente.")

    def get_col_idx(*keys):
        for k in keys:
            for h, idx in headers.items():
                if _norm(k) in h:
                    return idx
        return None

    col_nombre = get_col_idx("nombre")
    col_cedula = get_col_idx("cedula", "cédula", "ci")
    col_desvinculado = get_col_idx("desvinculado", "estado", "enviado")

    if col_cedula is None:
        raise HTTPException(status_code=400, detail="Columna Cédula requerida no encontrada.")

    to_process = 0
    already_processed = 0
    details = []
    
    empty_count = 0
    for r_idx in range(header_r_idx + 1, len(values)):
        row = values[r_idx]
        
        def get_val(c_idx):
            if c_idx is not None and c_idx < len(row):
                return str(row[c_idx] or "").strip()
            return ""

        nombre_val = get_val(col_nombre) if col_nombre is not None else ""
        cedula_val = get_val(col_cedula)
        desv_val = get_val(col_desvinculado)
        
        if not cedula_val:
            empty_count += 1
            if empty_count > 10:
                break
            continue
            
        empty_count = 0
        if "✅" in desv_val or "si" in desv_val.lower() or "desvinculado" in desv_val.lower():
            already_processed += 1
        else:
            to_process += 1
            if len(details) < 50:
                details.append({"nombre": nombre_val or "Sin Nombre", "cedula": cedula_val})

    return PreviewResponse(
        sheet_name=req.sheet_name,
        students_to_process=to_process,
        students_already_processed=already_processed,
        student_details=details
    )

@router.post("/excel/egreso", response_model=BulkResult)
async def import_egreso_onedrive(req: DiplomadosUrlRequest) -> BulkResult:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        range_data = await graph.get(f"/shares/{encoded_url}/driveItem/workbook/worksheets('{req.sheet_name}')/usedRange")
    except Exception as e:
        if "ItemNotFound" in str(e):
            raise HTTPException(status_code=400, detail=f"La pestaña '{req.sheet_name}' no existe o el archivo no es un Excel válido.")
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo de Excel. {e}")

    values = range_data.get("values", [])
    if not values:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    start_row = range_data.get("rowIndex", 0)
    start_col = range_data.get("columnIndex", 0)

    header_r_idx = None
    headers = {}
    
    for r_idx, row in enumerate(values[:6]):
        row_vals = [str(v or "").strip().lower() for v in row]
        if any("cedula" in v or "cédula" in v or "ci" in v for v in row_vals):
            header_r_idx = r_idx
            for c_idx, val in enumerate(row_vals):
                if val:
                    headers[_norm(val)] = c_idx
            break
            
    if header_r_idx is None:
        raise HTTPException(status_code=400, detail="No se encontró la columna 'Cédula'.")

    def get_col_idx(*keys):
        for k in keys:
            for h, idx in headers.items():
                if _norm(k) in h:
                    return idx
        return None

    col_cedula = get_col_idx("cedula", "cédula", "ci")
    col_desvinculado = get_col_idx("desvinculado", "estado", "enviado")

    if col_cedula is None:
        raise HTTPException(status_code=400, detail="Columna Cédula requerida no encontrada.")

    max_col = len(values[header_r_idx])
    
    async def patch_header(c_idx, val):
        abs_r = start_row + header_r_idx
        abs_c = start_col + c_idx
        try:
            await graph.patch(f"/shares/{encoded_url}/driveItem/workbook/worksheets('{req.sheet_name}')/cell(row={abs_r},column={abs_c})", {"values": [[val]]})
        except:
            pass

    if col_desvinculado is None:
        col_desvinculado = max_col
        max_col += 1
        await patch_header(col_desvinculado, "Desvinculado")

    result = BulkResult(succeeded=[], failed=[])
    
    async def process_row(r_idx, row):
        def get_val(c_idx):
            if c_idx is not None and c_idx < len(row):
                return str(row[c_idx] or "").strip()
            return ""

        cedula = get_val(col_cedula)
        desvinculado = get_val(col_desvinculado)
        
        if not cedula or cedula == "None":
            return
        if "✅" in desvinculado or "si" in desvinculado.lower() or "desvinculado" in desvinculado.lower():
            return

        error = None
        
        # 1. Canvas suspend
        canvas_email = None
        try:
            c_user = await canvas.get(f"/accounts/{_ACCOUNT}/users/sis_user_id:{cedula}")
            user_id = c_user.get("id")
            if user_id:
                await canvas.delete(f"/accounts/{_ACCOUNT}/users/{user_id}")
                canvas_email = c_user.get("email")
            else:
                error = "Usuario no encontrado en Canvas"
        except Exception as e:
            if "404" in str(e):
                error = "Usuario no encontrado en Canvas"
            else:
                error = f"Error Canvas: {e}"
        
        # 2. Teams disable
        teams_suspended = False
        if not error and canvas_email:
            try:
                teams_users = await graph.get("/users", params={"$filter": f"userPrincipalName eq '{canvas_email}'"})
                if teams_users and isinstance(teams_users.get("value"), list) and len(teams_users["value"]) > 0:
                    t_user_id = teams_users["value"][0]["id"]
                    await graph.patch(f"/users/{t_user_id}", {"accountEnabled": False})
                    teams_suspended = True
                else:
                    error = "Creado OK en Canvas, pero no encontrado en Teams"
            except Exception as te:
                error = f"Creado OK en Canvas, Error Teams: {te}"

        # calculate absolute row and column addresses
        abs_r = start_row + r_idx
        abs_col_desv = start_col + col_desvinculado

        async def patch_cell(c, val):
            try:
                await graph.patch(
                    f"/shares/{encoded_url}/driveItem/workbook/worksheets('{req.sheet_name}')/cell(row={abs_r},column={c})",
                    {"values": [[val]]}
                )
            except Exception as e:
                pass 

        if not error or "Creado OK" in str(error):
            result.succeeded.append({"cedula": cedula, "nombre": canvas_email})
            await patch_cell(abs_col_desv, "✅")
        else:
            result.failed.append({"input": {"cedula": cedula}, "error": error})
            await patch_cell(abs_col_desv, f"❌ Error: {error}")

    tasks = []
    empty_count = 0
    for r_idx in range(header_r_idx + 1, len(values)):
        row = values[r_idx]
        
        def get_val(c_idx):
            if c_idx is not None and c_idx < len(row):
                return str(row[c_idx] or "").strip()
            return ""

        cedula_val = get_val(col_cedula)
        
        if not cedula_val:
            empty_count += 1
            if empty_count > 10:
                break
            continue
            
        empty_count = 0
        tasks.append(process_row(r_idx, row))
        
    if len(tasks) > 50:
        raise HTTPException(status_code=400, detail=f"Límite de seguridad excedido: Intentas procesar {len(tasks)} alumnos a la vez (Máximo 50 permitidos). Revisa el archivo para evitar accidentes.")

    batch_size = 5
    for i in range(0, len(tasks), batch_size):
        await asyncio.gather(*tasks[i:i+batch_size])

    return result
'''

content += "\n" + new_code

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Appended egreso endpoints")
