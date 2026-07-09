import sys

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. preview_diplomados_onedrive
target_1 = '''    headers = []
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
    for i, h in enumerate(headers):'''

repl_1 = '''    sample_rows = []
    header_row_idx, headers_dict, headers_raw = _find_header_row_and_headers(ws)
            
    if not header_row_idx:
        raise HTTPException(status_code=400, detail="No se encontró la fila de encabezados.")

    headers = [h for h in headers_raw if h] # Just for returning to frontend
    
    col_estado = -1
    col_nombre = -1
    col_cedula = -1
    for i, h in enumerate(headers_raw):
        if not h: continue'''

if target_1 in content:
    content = content.replace(target_1, repl_1)
    print("Replaced preview_diplomados")
else:
    print("Failed to replace preview_diplomados")

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)
