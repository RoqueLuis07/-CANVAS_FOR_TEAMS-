    col_nombre = get_col_idx("nombre")
    col_cedula = get_col_idx("cedula", "cédula", "ci")
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
    col_usuario = get_col_idx("usuario")

    students_to_process = 0
    student_details = []

    for r_idx in range(header_row_idx + 1, ws.max_row + 1):
        nombre = str(ws.cell(row=r_idx, column=col_nombre).value or "").strip()
        cedula = str(ws.cell(row=r_idx, column=col_cedula).value or "").strip()
        enviado = str(ws.cell(row=r_idx, column=col_enviado).value or "").strip().lower() if col_enviado else ""
        usuario_val = str(ws.cell(row=r_idx, column=col_usuario).value or "").strip() if col_usuario else ""

        if not nombre or not cedula or cedula == "None":
            continue

        if "✅" in enviado or enviado in ["si", "yes", "true", "enviado", "ok"] or "creado ok" in enviado or "ya exist" in enviado or (usuario_val and "@" in usuario_val):
            continue

        students_to_process += 1
        if len(student_details) < 100:
            student_details.append({
                "nombre": nombre,
                "cedula": cedula
            })

    return {
        "students_to_process": students_to_process,
        "student_details": student_details
    }


@router.post("/excel/masivo", summary="Importar Masivamente desde OneDrive (Sin Matriculación)", response_model=BulkResult)
async def import_masivo_onedrive(req: DiplomadosUrlRequest) -> BulkResult:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo de OneDrive. {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo descargado no es un Excel válido.")

