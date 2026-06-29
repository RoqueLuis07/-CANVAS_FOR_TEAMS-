# -*- coding: utf-8 -*-
import sys
import io

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Preview endpoint
preview_code = '''
class PreviewResponse(BaseModel):
    sheet_name: str
    students_to_process: int
    students_already_processed: int
    total_rows: int

@router.post("/excel/diplomados/preview", summary="Pre-visualizar planilla de Diplomados")
async def preview_diplomados_onedrive(req: DiplomadosUrlRequest) -> PreviewResponse:
    if not req.url or "http" not in req.url:
        raise HTTPException(status_code=400, detail="URL inválida.")
    
    encoded_url = _encode_share_url(req.url)
    try:
        contents = await graph.get_raw(f"/shares/{encoded_url}/driveItem/content")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo. {e}")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail="El archivo no es un Excel válido.")

    if req.sheet_name not in wb.sheetnames:
        raise HTTPException(status_code=400, detail=f"La pestaña '{req.sheet_name}' no existe. Disponibles: {', '.join(wb.sheetnames)}")

    ws = wb[req.sheet_name]
    
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
    
    if not col_nombre or not col_cedula:
        raise HTTPException(status_code=400, detail="Columnas requeridas no encontradas.")

    to_process = 0
    already_processed = 0
    
    empty_count = 0
    for r_idx in range(header_row_idx + 1, ws.max_row + 1):
        nombre_val = str(ws.cell(row=r_idx, column=col_nombre).value or "").strip()
        cedula_val = str(ws.cell(row=r_idx, column=col_cedula).value or "").strip()
        
        if not nombre_val and not cedula_val:
            empty_count += 1
            if empty_count > 10:
                break
            continue
            
        empty_count = 0
        enviado = ""
        if col_enviado:
            enviado = str(ws.cell(row=r_idx, column=col_enviado).value or "").strip()
            
        if "?" in enviado or enviado.lower() in ["si", "yes", "true", "enviado"]:
            already_processed += 1
        else:
            to_process += 1
            
    wb.close()
    return PreviewResponse(
        sheet_name=req.sheet_name,
        students_to_process=to_process,
        students_already_processed=already_processed,
        total_rows=to_process + already_processed
    )

'''

# Inject preview before import_diplomados_onedrive
if "@router.post(\\"/excel/diplomados\\"" in content:
    content = content.replace('@router.post("/excel/diplomados"', preview_code + '\\n@router.post("/excel/diplomados"')

# Add MAX BATCH SIZE check inside import_diplomados_onedrive
limit_code = '''
        if len(tasks) > 50:
            raise HTTPException(status_code=400, detail=f"Límite de seguridad excedido: Intentas procesar {len(tasks)} alumnos a la vez (Máximo 50 permitidos). Revisa el archivo para evitar accidentes.")
'''

if 'tasks.append(process_row(r_idx))' in content:
    content = content.replace('tasks.append(process_row(r_idx))\\n            \\n        batch_size = 5', 'tasks.append(process_row(r_idx))\\n            \\n' + limit_code + '        batch_size = 5')

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated backend")
