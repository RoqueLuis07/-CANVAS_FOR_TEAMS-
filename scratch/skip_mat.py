import sys
with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix preview_matriculaciones_onedrive
target_preview = '''        estado_val = row_vals[col_enviado] if col_enviado >= 0 else ""
        if estado_val.lower() == "ok" or "error" in estado_val.lower():
            students_already_processed += 1
        else:
            students_to_process += 1'''

replacement_preview = '''        estado_val = row_vals[col_enviado] if col_enviado >= 0 else ""
        if estado_val.lower() == "ok" or "matriculado" in estado_val.lower():
            students_already_processed += 1
        else:
            students_to_process += 1'''

if target_preview in content:
    content = content.replace(target_preview, replacement_preview)
    print("Fixed preview count")
else:
    print("Could not find target_preview")

# Fix import_matriculaciones_onedrive to skip OK rows
target_import = '''    async def process_row(r_idx):
        user_val = str(ws.cell(row=r_idx, column=user_col).value or "").strip()
        if not user_val:
            return None
        
        canvas_val = str(ws.cell(row=r_idx, column=canvas_col).value or "").strip() if canvas_col else ""'''

replacement_import = '''    async def process_row(r_idx):
        user_val = str(ws.cell(row=r_idx, column=user_col).value or "").strip()
        if not user_val:
            return None
            
        estado_val = str(ws.cell(row=r_idx, column=env_col).value or "").strip().lower()
        if estado_val == "ok" or "matriculado" in estado_val:
            return None
        
        canvas_val = str(ws.cell(row=r_idx, column=canvas_col).value or "").strip() if canvas_col else ""'''

if target_import in content:
    content = content.replace(target_import, replacement_import)
    print("Fixed import skip")
else:
    print("Could not find target_import")

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)
