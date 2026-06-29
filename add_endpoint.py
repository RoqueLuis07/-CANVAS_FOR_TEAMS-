import os

ENDPOINT_CODE = '''

# -------------------------------------------------------------------------------
# Diplomados (Lectura y Escritura de Planilla Original)
# -------------------------------------------------------------------------------

@router.post("/excel/diplomados", summary="Procesar planilla de Diplomados (retorna el archivo modificado)")
async def import_diplomados(file: UploadFile = File(...)):
    _validate_file(file)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande.")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Archivo Excel inválido.")

    _ACCOUNT_LOCAL = settings.canvas_account_id

    # Buscar en cada hoja
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
        # Encontrar la fila de cabeceras (asumimos que está entre las filas 1 y 5)
        header_row_idx = None
        headers = {}
        for row_idx in range(1, min(6, ws.max_row + 1)):
            row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip().lower() for c in range(1, ws.max_column + 1)]
            if any("nombre" in v for v in row_vals) and any("cedula" in v or "cédula" in v for v in row_vals):
                header_row_idx = row_idx
                for col_idx, val in enumerate(row_vals, 1):
                    headers[_norm(val)] = col_idx
                break
        
        if not header_row_idx:
            continue # No headers found in this sheet, skip to next

        # Identificar columnas clave (buscando variaciones)
        def get_col_idx(*keys):
            for k in keys:
                for h, idx in headers.items():
                    if _norm(k) in h:
                        return idx
            return None

        col_nombre = get_col_idx("nombre")
        col_cedula = get_col_idx("cedula", "cédula", "ci")
        col_correo = get_col_idx("correo")
        
        # Buscar o crear columnas para resultados
        col_usuario = get_col_idx("usuario")
        col_contra = get_col_idx("contrasena", "contraseña", "clave")
        col_enviado = get_col_idx("enviado", "estado")

        if not col_nombre or not col_cedula:
            continue # Faltan columnas vitales

        # Si no existen las columnas de resultado, las creamos al final
        next_col = ws.max_column + 1
        if not col_usuario:
            col_usuario = next_col
            ws.cell(row=header_row_idx, column=col_usuario, value="Usuario").font = Font(bold=True)
            next_col += 1
        if not col_contra:
            col_contra = next_col
            ws.cell(row=header_row_idx, column=col_contra, value="Contraseña").font = Font(bold=True)
            next_col += 1
        if not col_enviado:
            col_enviado = next_col
            ws.cell(row=header_row_idx, column=col_enviado, value="Enviado").font = Font(bold=True)
        
        # Procesar las filas de datos
        async def process_row(r_idx):
            nombre = str(ws.cell(row=r_idx, column=col_nombre).value or "").strip()
            cedula = str(ws.cell(row=r_idx, column=col_cedula).value or "").strip()
            correo = str(ws.cell(row=r_idx, column=col_correo).value or "").strip() if col_correo else ""
            
            enviado = str(ws.cell(row=r_idx, column=col_enviado).value or "").strip()
            
            if not nombre or not cedula:
                return # Fila vacía
            if "?" in enviado or enviado.lower() in ["si", "yes", "true", "enviado"]:
                return # Ya procesado

            # 1. Generar credenciales
            creds = generate_credentials(nombre, cedula, settings.institutional_domain)
            login_id = creds["email"]
            pwd = creds["password"]
            
            error = None
            
            # 2. Crear en Canvas
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
            
            # 3. Crear en Teams (si no hubo error grave)
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
                    # Graph throws error if user already exists, which is common
                    # We might want to ignore "already exists" errors or log them
                    if "already exists" not in str(e).lower():
                        error = str(e)
            
            # 4. Enviar email (opcional, asume 'diplomado' por defecto)
            if not error and correo:
                try:
                    await send_welcome_email(
                        to_email=correo, 
                        full_name=creds["full_name"], 
                        institutional_email=login_id,
                        login_id=login_id, 
                        password=pwd, 
                        platform="both",
                        program_type="diplomado", 
                        program_name=sheet_name,
                        extra_cc=None,
                        attachments=get_program_attachments("diplomado")
                    )
                except Exception as e:
                    pass # Ignore email error to not fail the whole row if account was created
            
            # 5. Escribir resultados en el Excel
            if not error:
                ws.cell(row=r_idx, column=col_usuario, value=login_id)
                ws.cell(row=r_idx, column=col_contra, value=pwd)
                ws.cell(row=r_idx, column=col_enviado, value="?")
                
                # Pintar de verde el tick
                ws.cell(row=r_idx, column=col_enviado).font = Font(color="00B050", bold=True)
            else:
                ws.cell(row=r_idx, column=col_enviado, value=f"? Error: {error}")
                ws.cell(row=r_idx, column=col_enviado).font = Font(color="FF0000")

        # Correr en paralelo (batch de a 5 para no saturar)
        tasks = []
        for r_idx in range(header_row_idx + 1, ws.max_row + 1):
            tasks.append(process_row(r_idx))
            
        # Agrupar en batches
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i+batch_size])

    # Devolver el archivo modificado
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = file.filename.replace(".xlsx", "_procesado.xlsx") if file.filename else "diplomados_procesado.xlsx"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
'''

with open("Backend/app/routers/excel.py", "a", encoding="utf-8") as f:
    f.write(ENDPOINT_CODE)
