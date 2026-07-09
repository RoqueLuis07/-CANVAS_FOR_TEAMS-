async def preview_diplomados_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inv├ílida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo. {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo no es un Excel v├ílido.")

    if req.sheet_name not in wb.sheetnames:
        raise HTTPException(status_code=400, detail=f"La pesta├▒a '{req.sheet_name}' no existe. Disponibles: {', '.join(wb.sheetnames)}")

    ws = wb[req.sheet_name]

    headers = []
    sample_rows = []
    header_row_idx = None
    
    for row_idx in range(1, min(10, ws.max_row + 1)):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, ws.max_column + 1)]
        valid_cols = [v for v in row_vals if v]
        if len(valid_cols) > 1 and any(keyword in " ".join(valid_cols).lower() for keyword in ["nombre", "curso", "usuario", "correo", "cedula", "ci"]):
            header_row_idx = row_idx
            headers = [v for v in row_vals if v]
            break
            
    if not header_row_idx:
        raise HTTPException(status_code=400, detail="No se encontró la fila de encabezados.")

    col_estado = -1
    col_nombre = -1
    col_cedula = -1
    for i, h in enumerate(headers):
        h_lower = h.lower()
        if "estado" in h_lower or ("canvas" in h_lower and "id" in h_lower):
            col_estado = i
        if "nombre" in h_lower:
            if col_nombre == -1: col_nombre = i
        if "cedula" in h_lower or "cédula" in h_lower or "ci" in h_lower:
            if col_cedula == -1: col_cedula = i

    students_to_process = 0
    students_already_processed = 0
    student_details = []

    for row_idx in range(header_row_idx + 1, ws.max_row + 1):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, len(headers) + 1)]
        
        # Check if the row has at least a name
        if not any(row_vals):
            continue
            
        estado_val = row_vals[col_estado] if col_estado >= 0 else ""
        if "✅" in estado_val or estado_val.lower() in ["creado", "ok", "si"]:
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