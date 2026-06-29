import os

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re

# Base64 function needs to be at the top or inside the endpoint
NEW_ENDPOINT = '''
class DiplomadosUrlRequest(BaseModel):
    url: str

import base64

def _encode_share_url(url: str) -> str:
    encoded = base64.b64encode(url.encode('utf-8')).decode('utf-8')
    encoded = encoded.replace('+', '-').replace('/', '_').rstrip('=')
    return 'u!' + encoded

@router.post("/excel/diplomados", summary="Procesar planilla de Diplomados directo en OneDrive")
async def import_diplomados_onedrive(req: DiplomadosUrlRequest) -> BulkResult:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    
    encoded_url = _encode_share_url(req.url)
    
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo de OneDrive. Verifica la URL y los permisos. Detalle: {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo descargado no es un Excel válido.")

    _ACCOUNT_LOCAL = settings.canvas_account_id
    result = BulkResult()

    # Buscar en cada hoja
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
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
            continue

        def get_col_idx(*keys):
            for k in keys:
                for h, idx in headers.items():
                    if _norm(k) in h:
                        return idx
            return None

        col_nombre = get_col_idx("nombre")
        col_cedula = get_col_idx("cedula", "cédula", "ci")
        col_correo = get_col_idx("correo")
        
        col_usuario = get_col_idx("usuario")
        col_contra = get_col_idx("contrasena", "contraseña", "clave")
        col_enviado = get_col_idx("enviado", "estado")

        if not col_nombre or not col_cedula:
            continue

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
        
        async def process_row(r_idx):
            nombre = str(ws.cell(row=r_idx, column=col_nombre).value or "").strip()
            cedula = str(ws.cell(row=r_idx, column=col_cedula).value or "").strip()
            correo = str(ws.cell(row=r_idx, column=col_correo).value or "").strip() if col_correo else ""
            
            enviado = str(ws.cell(row=r_idx, column=col_enviado).value or "").strip()
            
            if not nombre or not cedula or cedula == "None":
                return
            if "?" in enviado or enviado.lower() in ["si", "yes", "true", "enviado"]:
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
                        program_name=sheet_name,
                        extra_cc=None,
                        attachments=get_program_attachments("diplomado")
                    )
                except Exception as e:
                    pass
            
            if not error:
                ws.cell(row=r_idx, column=col_usuario, value=login_id)
                ws.cell(row=r_idx, column=col_contra, value=pwd)
                ws.cell(row=r_idx, column=col_enviado, value="?")
                ws.cell(row=r_idx, column=col_enviado).font = Font(color="00B050", bold=True)
                result.succeeded.append({"cedula": cedula, "nombre": creds["full_name"]})
            else:
                ws.cell(row=r_idx, column=col_enviado, value=f"? Error")
                ws.cell(row=r_idx, column=col_enviado).font = Font(color="FF0000")
                result.failed.append({"input": {"cedula": cedula}, "error": error})

        tasks = []
        for r_idx in range(header_row_idx + 1, ws.max_row + 1):
            tasks.append(process_row(r_idx))
            
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            import asyncio
            await asyncio.gather(*tasks[i:i+batch_size])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    try:
        await graph.put_raw(f"/shares/{encoded_url}/driveItem/content", output.getvalue())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar el archivo actualizado en OneDrive. {e}")

    return result
'''

import re
old_endpoint_pattern = r'@router\.post\("/excel/diplomados".*?return StreamingResponse\([\s\S]*?\)'
new_code = re.sub(old_endpoint_pattern, NEW_ENDPOINT.strip(), code, flags=re.DOTALL)

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(new_code)
