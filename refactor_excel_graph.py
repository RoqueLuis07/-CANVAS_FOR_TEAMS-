# -*- coding: utf-8 -*-
import sys
import io

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start of the relevant section
marker = "class DiplomadosUrlRequest(BaseModel):"
idx = content.find(marker)
if idx == -1:
    print("Marker not found")
    sys.exit(1)

new_code = '''class DiplomadosUrlRequest(BaseModel):
    url: str
    sheet_name: str

class PreviewResponse(BaseModel):
    sheet_name: str
    students_to_process: int
    students_already_processed: int
    student_details: list[dict]

def _encode_share_url(url: str) -> str:
    import base64
    b64 = base64.b64encode(url.encode()).decode()
    b64 = b64.replace("/", "_").replace("+", "-").rstrip("=")
    return f"u!{b64}"

@router.post("/excel/diplomados/preview", response_model=PreviewResponse)
async def preview_diplomados_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
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
    
    # We only look at the first 6 rows to find the headers
    for r_idx, row in enumerate(values[:6]):
        row_vals = [str(v or "").strip().lower() for v in row]
        if any("nombre" in v for v in row_vals) and any("cedula" in v or "cédula" in v or "ci" in v for v in row_vals):
            header_r_idx = r_idx
            for c_idx, val in enumerate(row_vals):
                if val:
                    headers[_norm(val)] = c_idx
            break
            
    if header_r_idx is None:
        raise HTTPException(status_code=400, detail="No se encontraron las columnas 'Nombre' y 'Cédula'.")

    def get_col_idx(*keys):
        for k in keys:
            for h, idx in headers.items():
                if _norm(k) in h:
                    return idx
        return None

    col_nombre = get_col_idx("nombre")
    col_cedula = get_col_idx("cedula", "cédula", "ci")
    col_enviado = get_col_idx("enviado", "estado")

    if col_nombre is None or col_cedula is None:
        raise HTTPException(status_code=400, detail="Columnas requeridas no encontradas.")

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

        nombre_val = get_val(col_nombre)
        cedula_val = get_val(col_cedula)
        enviado_val = get_val(col_enviado)
        
        if not nombre_val and not cedula_val:
            empty_count += 1
            if empty_count > 10:
                break
            continue
            
        empty_count = 0
        if "✅" in enviado_val or "si" in enviado_val.lower() or "enviado" in enviado_val.lower():
            already_processed += 1
        else:
            to_process += 1
            if len(details) < 50:
                details.append({"nombre": nombre_val, "cedula": cedula_val})

    return PreviewResponse(
        sheet_name=req.sheet_name,
        students_to_process=to_process,
        students_already_processed=already_processed,
        student_details=details
    )

@router.post("/excel/diplomados", response_model=BulkResult)
async def import_diplomados_onedrive(req: DiplomadosUrlRequest) -> BulkResult:
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

    # The starting row/col index of this used range relative to the worksheet (0-based)
    start_row = range_data.get("rowIndex", 0)
    start_col = range_data.get("columnIndex", 0)

    header_r_idx = None
    headers = {}
    
    for r_idx, row in enumerate(values[:6]):
        row_vals = [str(v or "").strip().lower() for v in row]
        if any("nombre" in v for v in row_vals) and any("cedula" in v or "cédula" in v or "ci" in v for v in row_vals):
            header_r_idx = r_idx
            for c_idx, val in enumerate(row_vals):
                if val:
                    headers[_norm(val)] = c_idx
            break
            
    if header_r_idx is None:
        raise HTTPException(status_code=400, detail="No se encontraron las columnas 'Nombre' y 'Cédula'.")

    def get_col_idx(*keys):
        for k in keys:
            for h, idx in headers.items():
                if _norm(k) in h:
                    return idx
        return None

    col_nombre = get_col_idx("nombre")
    col_cedula = get_col_idx("cedula", "cédula", "ci")
    col_correo = get_col_idx("correo", "email")
    
    col_usuario = get_col_idx("usuario", "user")
    col_contra = get_col_idx("contrasena", "contraseña", "clave", "pass")
    col_enviado = get_col_idx("enviado", "estado")

    if col_nombre is None or col_cedula is None:
        raise HTTPException(status_code=400, detail="Columnas requeridas no encontradas.")

    max_col = len(values[header_r_idx])
    
    # We patch missing headers if necessary
    async def patch_header(c_idx, val):
        abs_r = start_row + header_r_idx
        abs_c = start_col + c_idx
        try:
            await graph.patch(f"/shares/{encoded_url}/driveItem/workbook/worksheets('{req.sheet_name}')/cell(row={abs_r},column={abs_c})", {"values": [[val]]})
        except:
            pass

    if col_usuario is None:
        col_usuario = max_col
        max_col += 1
        await patch_header(col_usuario, "Usuario")
    if col_contra is None:
        col_contra = max_col
        max_col += 1
        await patch_header(col_contra, "Contraseña")
    if col_enviado is None:
        col_enviado = max_col
        max_col += 1
        await patch_header(col_enviado, "Enviado")

    result = BulkResult(succeeded=[], failed=[])
    
    async def process_row(r_idx, row):
        def get_val(c_idx):
            if c_idx is not None and c_idx < len(row):
                return str(row[c_idx] or "").strip()
            return ""

        nombre = get_val(col_nombre)
        cedula = get_val(col_cedula)
        correo = get_val(col_correo) if col_correo is not None else ""
        enviado = get_val(col_enviado)
        
        if not nombre or not cedula or cedula == "None":
            return
        if "✅" in enviado or enviado.lower() in ["si", "yes", "true", "enviado"]:
            return

        creds = generate_credentials(nombre, cedula, settings.institutional_domain)
        login_id = creds["email"]
        pwd = creds["password"]
        error = None
        
        try:
            await canvas.post(f"/accounts/{_ACCOUNT_LOCAL}/users", {
                "user": {"name": creds["full_name"]},
                "pseudonym": {
                    "unique_id": login_id, "sis_user_id": cedula,
                    "password": pwd, "send_confirmation": False,
                },
                "communication_channel": {
                    "type": "email", "address": login_id,
                    "skip_confirmation": True,
                },
            })
        except Exception as e:
            error = str(e)
        
        if not error:
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
                await graph.assign_license(au["id"], settings.azure_sku_students)
            except Exception as e:
                if "already exists" not in str(e).lower() and "Request_BadRequest" not in str(e):
                    error = str(e)
        
        email_sent = False
        if not error and correo and correo != "None":
            try:
                await send_welcome_email(
                    to_email=correo, 
                    full_name=creds["full_name"], 
                    institutional_email=login_id,
                    login_id=login_id, 
                    password=pwd, 
                    platform="both",
                    program_type="diplomado", 
                    program_name=req.sheet_name,
                    extra_cc=None,
                    attachments=get_program_attachments("diplomado")
                )
                email_sent = True
            except Exception as e:
                error = f"Creado OK, pero falló el correo: {e}"
        elif not error and (not correo or correo == "None"):
            error = "Creado OK, pero no hay correo asignado"
        
        # calculate absolute row and column addresses
        abs_r = start_row + r_idx
        abs_col_enviado = start_col + col_enviado
        abs_col_user = start_col + col_usuario
        abs_col_pwd = start_col + col_contra

        async def patch_cell(c, val):
            try:
                await graph.patch(
                    f"/shares/{encoded_url}/driveItem/workbook/worksheets('{req.sheet_name}')/cell(row={abs_r},column={c})",
                    {"values": [[val]]}
                )
            except Exception as e:
                pass # ignore cell update errors if any (or log them)

        if not error or "Creado OK" in str(error):
            result.succeeded.append({"cedula": cedula, "nombre": creds["full_name"]})
            
            if email_sent:
                # Patch cells individually
                await patch_cell(abs_col_user, login_id)
                await patch_cell(abs_col_pwd, pwd)
                await patch_cell(abs_col_enviado, "✅")
            else:
                await patch_cell(abs_col_user, login_id)
                await patch_cell(abs_col_pwd, pwd)
                await patch_cell(abs_col_enviado, f"✅? {error}")
        else:
            result.failed.append({"input": {"cedula": cedula}, "error": error})
            await patch_cell(abs_col_enviado, f"❌ Error: {error}")

    tasks = []
    empty_count = 0
    for r_idx in range(header_r_idx + 1, len(values)):
        row = values[r_idx]
        
        def get_val(c_idx):
            if c_idx is not None and c_idx < len(row):
                return str(row[c_idx] or "").strip()
            return ""

        nombre_val = get_val(col_nombre)
        cedula_val = get_val(col_cedula)
        
        if not nombre_val and not cedula_val:
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

new_content = content[:idx] + new_code

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Replacement successful")
