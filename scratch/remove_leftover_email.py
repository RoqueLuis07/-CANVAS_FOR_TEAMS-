import re

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the leftover 'Otros CC'
content = re.sub(r'<input type="text" id="ci_cc_otros".*?</div>\s*', '', content, flags=re.DOTALL)

# Remove the 'Enviar correo de bienvenida con credenciales' block
content = re.sub(r'<div class="mb-4">\s*<div class="form-check">\s*<input class="form-check-input" type="checkbox" id="ci_enviar" checked>\s*<label class="form-check-label" for="ci_enviar">\s*Enviar correo de bienvenida con credenciales\s*</label>\s*</div>\s*</div>\s*', '', content, flags=re.DOTALL)

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(content)
