import sys
with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: preview_matriculaciones_onedrive
target1 = 'or "cedula" in v.lower() for v in row_vals'
replacement1 = 'or "cedula" in v.lower() or "sis" in v.lower() or "alumno" in v.lower() for v in row_vals'
if target1 in content:
    content = content.replace(target1, replacement1)
    print("Fix 1 applied")
else:
    print("Fix 1 failed")

# Fix 2: import_matriculaciones_onedrive
target2 = 'for keyword in ["usuario", "correo", "email", "cedula", "sis", "alumno", "rol", "canvas", "teams"]'
replacement2 = 'for keyword in ["usuario", "correo", "email", "cedula", "sis", "alumno"]'
if target2 in content:
    content = content.replace(target2, replacement2)
    print("Fix 2 applied")
else:
    print("Fix 2 failed")

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)
