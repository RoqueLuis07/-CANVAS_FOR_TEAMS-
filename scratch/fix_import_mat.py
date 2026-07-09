import sys
import re

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the hardcoded ws[1] header parsing in import_matriculaciones_onedrive
target = '''    ws = wb[req.sheet_name]
    headers = {c.value: c.column for c in ws[1] if c.value}
    
    # Identify columns
    user_col, canvas_col, teams_col, rol_col, env_col = None, None, None, None, None
    for h, col_idx in headers.items():'''

replacement = '''    ws = wb[req.sheet_name]
    
    # Find header row
    header_row_idx = 1
    headers = {}
    for row_idx in range(1, min(10, ws.max_row + 1)):
        row_vals = [c.value for c in ws[row_idx]]
        row_strs = [str(v).strip().lower() for v in row_vals if v is not None]
        if any(keyword in r for r in row_strs for keyword in ["usuario", "correo", "email", "cedula", "sis", "alumno", "rol", "canvas", "teams"]):
            header_row_idx = row_idx
            headers = {c.value: c.column for c in ws[row_idx] if c.value}
            break

    # Identify columns
    user_col, canvas_col, teams_col, rol_col, env_col = None, None, None, None, None
    for h, col_idx in headers.items():'''

if target in content:
    new_content = content.replace(target, replacement)
    
    # Also need to update where the data starts reading, which is hardcoded to range(2, ws.max_row + 1)
    target_loop = '''    for r_idx in range(2, ws.max_row + 1):
        tasks.append(process_row(r_idx))'''
    
    replacement_loop = '''    for r_idx in range(header_row_idx + 1, ws.max_row + 1):
        tasks.append(process_row(r_idx))'''
        
    if target_loop in new_content:
        new_content = new_content.replace(target_loop, replacement_loop)
        
        # Also fix the env_col check which writes to row=1
        target_env = '''    if not env_col:
        env_col = ws.max_column + 1
        ws.cell(row=1, column=env_col, value="Enviado")'''
        
        replacement_env = '''    if not env_col:
        env_col = ws.max_column + 1
        ws.cell(row=header_row_idx, column=env_col, value="Enviado")'''
        
        if target_env in new_content:
            new_content = new_content.replace(target_env, replacement_env)
            
            with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Successfully updated import_matriculaciones_onedrive to find headers dynamically.")
        else:
            print("Failed to find target_env")
    else:
        print("Failed to find target_loop")
else:
    print("Failed to find target")
