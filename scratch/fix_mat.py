import sys
with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix preview_matriculaciones_onedrive
target_preview = '''      for row_idx in range(1, min(10, ws.max_row + 1)):
          row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, ws.max_column + 1)]
          if any("usuario" in v.lower() or "correo" in v.lower() or "cedula" in v.lower() for v in row_vals):
              header_row_idx = row_idx'''

replacement_preview = '''      for row_idx in range(1, min(10, ws.max_row + 1)):
          row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, ws.max_column + 1)]
          if any("usuario" in v.lower() or "correo" in v.lower() or "cedula" in v.lower() or "sis" in v.lower() or "alumno" in v.lower() for v in row_vals):
              header_row_idx = row_idx'''

if target_preview in content:
    content = content.replace(target_preview, replacement_preview)
    print("Fixed preview_matriculaciones_onedrive!")
else:
    print("Could not find target_preview!")

# Fix import_matriculaciones_onedrive
target_import = '''      for row_idx in range(1, min(10, ws.max_row + 1)):
          row_vals = [c.value for c in ws[row_idx]]
          row_strs = [str(v).strip().lower() for v in row_vals if v is not None]
          if any(keyword in r for r in row_strs for keyword in ["usuario", "correo", "email", "cedula", "sis", "alumno", "rol", "canvas", "teams"]):
              header_row_idx = row_idx'''

replacement_import = '''      for row_idx in range(1, min(10, ws.max_row + 1)):
          row_vals = [c.value for c in ws[row_idx]]
          row_strs = [str(v).strip().lower() for v in row_vals if v is not None]
          # Match explicitly the user column to avoid matching the title row which might contain "canvas"
          if any(keyword in r for r in row_strs for keyword in ["usuario", "correo", "email", "cedula", "sis", "alumno"]):
              header_row_idx = row_idx'''

if target_import in content:
    content = content.replace(target_import, replacement_import)
    print("Fixed import_matriculaciones_onedrive!")
else:
    print("Could not find target_import!")

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)
