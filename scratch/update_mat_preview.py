import sys

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find preview_matriculaciones_onedrive
start_idx = content.find('async def preview_matriculaciones_onedrive(req: DiplomadosUrlRequest)')
if start_idx == -1:
    print('Failed to find start_idx')
    sys.exit(1)

# Find the end (start of import_matriculaciones_onedrive)
end_idx = content.find('@router.post("/excel/matriculaciones-onedrive"', start_idx)
if end_idx == -1:
    print('Failed to find end_idx')
    sys.exit(1)

new_func = '''async def preview_matriculaciones_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo: {e}")
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
        if any("usuario" in v.lower() or "correo" in v.lower() or "cedula" in v.lower() or "sis" in v.lower() or "alumno" in v.lower() for v in row_vals):
            header_row_idx = row_idx
            headers = row_vals
            break
            
    if not header_row_idx:
        raise HTTPException(status_code=400, detail="No se encontraron encabezados.")

    col_enviado = -1
    for i, h in enumerate(headers):
        if "estado" in h.lower() or "enviado" in h.lower():
            col_enviado = i

    students_to_process = 0
    students_already_processed = 0

    for row_idx in range(header_row_idx + 1, ws.max_row + 1):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, len(headers) + 1)]
        if not any(row_vals):
            continue
            
        estado_val = row_vals[col_enviado] if col_enviado >= 0 else ""
        if estado_val.lower() == "ok" or "error" in estado_val.lower():
            students_already_processed += 1
        else:
            students_to_process += 1
            
        if len(sample_rows) < 10:
            sample_rows.append(dict(zip(headers, row_vals)))
            
    wb.close()
    return PreviewResponse(
        sheet_name=req.sheet_name,
        students_to_process=students_to_process,
        students_already_processed=students_already_processed,
        headers=headers,
        sample_rows=sample_rows,
        student_details=[]
    )
'''

new_content = content[:start_idx] + new_func + '\n' + content[end_idx:]

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Successfully updated preview_matriculaciones_onedrive!')
