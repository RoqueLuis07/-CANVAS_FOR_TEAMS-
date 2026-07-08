import re

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove HTML block for CCs and Enviar checkbox
html_block_pattern = r'<div class="mb-3">\s*<label class="form-label">Copias de correo \(CC\)</label>.*?</label>\s*</div>\s*</div>'
content = re.sub(html_block_pattern, '', content, flags=re.DOTALL)

# Update JS in doCrearInd
content = content.replace("send_email:   document.getElementById('ci_enviar').checked,", "send_email:   false,")
content = content.replace("cc:           getCCs('ci')", "cc:           []")

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed email sending options from Creación Individual.")
