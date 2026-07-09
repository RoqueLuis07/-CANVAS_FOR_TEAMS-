import sys

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Find the start and end of preview_masivo_onedrive
start_idx = content.find('async def preview_masivo_onedrive(req: DiplomadosUrlRequest) -> dict:')
if start_idx == -1:
    print('Could not find start')
    sys.exit(1)

# Find the next function to know where to stop
end_idx = content.find('@router.post("/excel/masivo",', start_idx)
if end_idx == -1:
    print('Could not find end')
    sys.exit(1)

new_func = '''async def preview_masivo_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo de OneDrive. {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo descargado no es un Excel válido.")

    if req.sheet_name not in wb.sheetnames:
        raise HTTPException(status_code=400, detail=f"La pestaña '{req.sheet_name}' no existe.")

    ws = wb[req.sheet_name]
    
    headers = []
    sample_rows = []
    header_row_idx = None
    
    for row_idx in range(1, min(10, ws.max_row + 1)):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, ws.max_column + 1)]
        valid_cols = [v for v in row_vals if v]
        if len(valid_cols) > 1 and any(keyword in " ".join(valid_cols).lower() for keyword in ["nombre", "curso", "usuario", "correo", "cedula", "ci"]):
            header_row_idx = row_idx
            headers = row_vals
            break
            
    if not header_row_idx:
        raise HTTPException(status_code=400, detail="No se encontró la fila de encabezados.")

    col_estado = -1
    col_nombre = -1
    col_cedula = -1
    col_usuario = -1
    for i, h in enumerate(headers):
        h_lower = h.lower()
        if "estado" in h_lower or "enviado" in h_lower:
            col_estado = i
        if "nombre" in h_lower:
            if col_nombre == -1: col_nombre = i
        if "cedula" in h_lower or "cédula" in h_lower or "ci" in h_lower:
            if col_cedula == -1: col_cedula = i
        if "usuario" in h_lower:
            if col_usuario == -1: col_usuario = i

    students_to_process = 0
    students_already_processed = 0
    student_details = []

    for row_idx in range(header_row_idx + 1, ws.max_row + 1):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, len(headers) + 1)]
        
        if not any(row_vals):
            continue
            
        estado_val = row_vals[col_estado] if col_estado >= 0 else ""
        usuario_val = row_vals[col_usuario] if col_usuario >= 0 else ""
        
        if "no." in estado_val.lower() or estado_val.lower() in ["si", "yes", "true", "enviado", "ok"] or "creado ok" in estado_val.lower() or "ya exist" in estado_val.lower() or (usuario_val and "@" in usuario_val):
            students_already_processed += 1
        else:
            students_to_process += 1
            if len(student_details) < 10:
                student_details.append({
                    "nombre": row_vals[col_nombre] if col_nombre >= 0 else "",
                    "cedula": row_vals[col_cedula] if col_cedula >= 0 else ""
                })
            
        if len(sample_rows) < 10:
            sample_rows.append(dict(zip(headers, row_vals)))
            
    wb.close()
    return PreviewResponse(
        sheet_name=req.sheet_name,
        students_to_process=students_to_process,
        students_already_processed=students_already_processed,
        headers=headers,
        sample_rows=sample_rows,
        student_details=student_details
    )

'''

new_content = content[:start_idx] + new_func + "\n\n" + content[end_idx:]

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated preview_masivo_onedrive successfully!')
