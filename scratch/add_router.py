import re

with open('Backend/app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
content = re.sub(
    r'(from app.routers import \(\n(?:.*?)\n\))',
    r'\1\nfrom app.routers import matriculacion',
    content,
    flags=re.DOTALL
)

# Add to routers_to_load
content = re.sub(
    r'(\("Ingreso", ingreso\.router\),)',
    r'\1\n    ("Matriculacion", matriculacion.router),',
    content
)

with open('Backend/app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
