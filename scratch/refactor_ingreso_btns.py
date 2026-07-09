import re

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Masivo Buttons
html = re.sub(
    r'<div class="d-flex justify-content-end gap-2 mb-4">\s*<button type="button" class="btn btn-outline-secondary d-none".*?id="btnPreviewMasivo">.*?</button>\s*<button type="button" class="btn btn-primary" onclick="importMasivo\(\)" id="btnImportMasivo" disabled>\s*<i class="bi bi-cloud-arrow-up me-2"></i>Procesar Masiva\s*</button>\s*</div>',
    '''<div class="d-flex justify-content-end mb-4">
                    <button type="button" class="btn btn-primary" onclick="importMasivo()" id="btnImportMasivo" disabled>
                      <i class="bi bi-check-circle me-2"></i>Confirmar y Procesar
                    </button>
                  </div>''',
    html,
    flags=re.DOTALL
)

# Diplomado Buttons
html = re.sub(
    r'<div class="d-flex justify-content-end gap-2 mb-4">\s*<button type="button" class="btn btn-outline-secondary d-none".*?id="btnPreviewDiplomados">.*?</button>\s*<button type="button" class="btn btn-success text-white" onclick="importDiplomados\(\)" id="btnImportDiplomados" disabled>\s*<i class="bi bi-cloud-arrow-up me-2"></i>Procesar Diplomados\s*</button>\s*</div>',
    '''<div class="d-flex justify-content-end mb-4">
                    <button type="button" class="btn btn-success text-white" onclick="importDiplomados()" id="btnImportDiplomados" disabled>
                      <i class="bi bi-check-circle me-2"></i>Confirmar y Procesar
                    </button>
                  </div>''',
    html,
    flags=re.DOTALL
)

# Docentes Buttons
html = re.sub(
    r'<div class="d-flex justify-content-end gap-2 mb-4">\s*<button type="button" class="btn btn-outline-secondary d-none".*?id="btnPreviewDocentes">.*?</button>\s*<button type="button" class="btn btn-warning text-dark fw-bold" onclick="importDocentes\(\)" id="btnImportDocentes" disabled>\s*<i class="bi bi-cloud-arrow-up me-2"></i>Procesar Docentes\s*</button>\s*</div>',
    '''<div class="d-flex justify-content-end mb-4">
                    <button type="button" class="btn btn-warning text-dark fw-bold" onclick="importDocentes()" id="btnImportDocentes" disabled>
                      <i class="bi bi-check-circle me-2"></i>Confirmar y Procesar
                    </button>
                  </div>''',
    html,
    flags=re.DOTALL
)

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("ingreso.html buttons refactored via regex")
