async def preview_docentes_onedrive(req: DiplomadosUrlRequest) -> DocentesPreviewResponse:
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
    title_val = str(ws.cell(row=1, column=1).value or "").strip()
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
    col_curso_nombre = get_col_idx("nombre del curso", "curso", "diplomado")
    col_enviado = get_col_idx("enviado", "estado")
    
    col_cc = get_col_idx("cc", "copia")
    sheet_cc_list = []
    if col_cc:
        for r_idx in range(header_row_idx + 1, ws.max_row + 1):
            cc_val = str(ws.cell(row=r_idx, column=col_cc).value or "").strip()
            if cc_val:
                for email in cc_val.replace(";", ",").replace("\n", ",").split(","):
                    email = email.strip()
                    if "@" in email and email not in sheet_cc_list:
                        sheet_cc_list.append(email)

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

    return DocentesPreviewResponse(
        total_rows=ws.max_row - header_row_idx,
        valid_rows=len(rows)