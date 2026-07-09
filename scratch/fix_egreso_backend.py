import sys
import re

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add decorators and preview function above import_egreso_onedrive
new_code = '''
@router.post("/excel/egreso/preview", summary="Pre-visualizar planilla de Egreso/Eliminación")
async def preview_egreso_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
    """Previsualiza los usuarios que se darán de baja leyendo la planilla."""
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
    
    sample_rows = []
    
    header_row_idx, headers_dict, headers_raw = _find_header_row_and_headers(ws)
    
    if not header_row_idx:
        raise HTTPException(status_code=400, detail="No se encontró la fila de encabezados.")

    headers = [h for h in headers_raw if h]

    def get_col_idx(*keys):
        for k in keys:
            for h, idx in headers_dict.items():
                if _norm(k) in h:
                    return idx
        return None

    col_nombre = get_col_idx("nombre")
    col_correo = get_col_idx("correo", "email")
    col_enviado = get_col_idx("enviado", "estado")

    students_to_process = 0
    students_already_processed = 0
    student_details = []

    for row_idx in range(header_row_idx + 1, ws.max_row + 1):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, len(headers_raw) + 1)]
        
        if not any(row_vals):
            continue
            
        nombre = row_vals[col_nombre - 1] if col_nombre else ""
        correo = row_vals[col_correo - 1] if col_correo else ""
        enviado = (row_vals[col_enviado - 1] if col_enviado else "").lower()
        
        if not nombre or not correo:
            continue
            
        if "ok" in enviado or "eliminado" in enviado or "baja" in enviado or "enviado" in enviado:
            students_already_processed += 1
        else:
            students_to_process += 1
            if len(student_details) < 3:
                student_details.append({"nombre": nombre, "correo": correo})
                sample_rows.append(row_vals[:min(5, len(row_vals))])

    return PreviewResponse(
        headers=headers[:min(5, len(headers))],
        sample_rows=sample_rows,
        total_to_process=students_to_process,
        already_processed=students_already_processed,
        details=student_details
    )

@router.post("/excel/egreso/import", summary="Procesar planilla de Egreso/Eliminación")
async def import_egreso_onedrive'''

if 'def preview_egreso_onedrive' not in content:
    content = content.replace('async def import_egreso_onedrive', new_code)
    with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Backend logic injected successfully.")
else:
    print("Backend logic already exists.")
