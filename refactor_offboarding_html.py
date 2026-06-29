import sys

with open('Frontend/templates/unified_offboarding.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_content = """{% extends "base.html" %}
{% block title %}Desvinculación (Offboarding) | Canvas for Teams{% endblock %}

{% block content %}
<div class="row mb-4 align-items-center">
  <div class="col-auto">
    <h1 class="h3 mb-0 text-danger"><i class="bi bi-person-x-fill me-2"></i>Desvinculación Unificada</h1>
  </div>
</div>

<!-- Tabs -->
<ul class="nav nav-tabs mb-4" id="offboardingTabs" role="tablist">
  <li class="nav-item" role="presentation">
    <button class="nav-link active text-danger" id="individual-tab" data-bs-toggle="tab" data-bs-target="#individual" type="button" role="tab" aria-controls="individual" aria-selected="true">
      <i class="bi bi-person-dash me-2"></i>Egreso Individual
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link text-danger" id="masivo-tab" data-bs-toggle="tab" data-bs-target="#masivo" type="button" role="tab" aria-controls="masivo" aria-selected="false">
      <i class="bi bi-cloud-arrow-down-fill me-2"></i>Egreso Masivo (Enlace OneDrive)
    </button>
  </li>
</ul>

<div class="tab-content" id="offboardingTabsContent">
  <!-- Tab: Individual -->
  <div class="tab-pane fade show active" id="individual" role="tabpanel" aria-labelledby="individual-tab">
    <div class="row">
      <div class="col-md-6">
        <div class="card shadow-sm border-danger mb-4">
          <div class="card-header bg-danger text-white">
            <h5 class="mb-0"><i class="bi bi-search me-2"></i>Buscar Usuario a Desvincular</h5>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label text-danger fw-bold">Nombre del Docente o Alumno</label>
              <input type="text" class="form-control border-danger" id="searchInput" placeholder="Escriba para buscar en Canvas..." autocomplete="off">
              <div id="searchSpinner" class="spinner-border spinner-border-sm text-danger mt-2" style="display:none;" role="status"></div>
            </div>
            
            <div class="mb-3 row">
              <div class="col">
                <label class="form-label text-muted">ID SIS / Cédula</label>
                <input type="text" class="form-control" id="sysInput" readonly>
              </div>
              <div class="col">
                <label class="form-label text-muted">Email Institucional</label>
                <input type="email" class="form-control" id="emailInput" readonly>
              </div>
            </div>
            
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                Esta acción <strong>suspenderá</strong> la cuenta en Canvas y <strong>deshabilitará</strong> el inicio de sesión en Microsoft Teams. No se borrarán los historiales de calificaciones.
            </div>

            <div class="d-grid mt-4">
                <button class="btn btn-danger btn-lg" id="btnExecute" onclick="executeOffboarding()" disabled>
                    <i class="bi bi-person-x-fill me-2"></i>Ejecutar Desvinculación
                </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Tab: Masivo (OneDrive) -->
  <div class="tab-pane fade" id="masivo" role="tabpanel" aria-labelledby="masivo-tab">
    <div class="card shadow-sm mb-4 border-danger">
      <div class="card-header bg-danger text-white">
        <h5 class="mb-0"><i class="bi bi-cloud-arrow-down-fill me-2"></i>Desvinculación Masiva desde OneDrive</h5>
      </div>
      <div class="card-body">
        <div class="alert alert-info border-info">
          <i class="bi bi-info-circle-fill me-2"></i>
          <strong>¿Cómo funciona?</strong>
          <ol class="mb-0 mt-2">
            <li>Crea un Excel en OneDrive con la columna <strong>Cédula</strong> de los alumnos a dar de baja.</li>
            <li>Haz clic en Compartir -> "Cualquiera con el enlace puede editar" y pega el link aquí.</li>
            <li>El sistema suspenderá las cuentas y escribirá un "✅" automáticamente en la columna <strong>Desvinculado</strong> de tu archivo Excel.</li>
          </ol>
        </div>
        
        <div class="row">
          <div class="col-md-8">
            <div class="mb-3">
              <label class="form-label fw-bold">Enlace del Excel en OneDrive</label>
              <input type="url" class="form-control border-danger" id="urlEgresoOneDrive" placeholder="https://usilparaguay-my.sharepoint.com/:x:/g/personal/...">
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Nombre de la Pestaña</label>
              <input type="text" class="form-control" id="sheetEgresoOneDrive" placeholder="Ej: Bajas Mayo">
            </div>
          </div>
          <div class="col-md-4 d-flex align-items-end mb-3">
            <button class="btn btn-danger w-100 p-3" id="btnEgresoOneDrive" onclick="openEgresoOneDrive()">
              <i class="bi bi-magic me-2"></i>Pre-visualizar y Ejecutar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
// Logic for individual offboarding is already in main.js or here.
// In the original file there was a script tag, we will keep its content if we need to, but it was just initialization for typeahead probably.
// Wait, let's inject the old script content just in case.
"""

# Extract the old script content
start_idx = content.find('<script>')
if start_idx != -1:
    old_script = content[start_idx + 8 : content.find('</script>', start_idx)]
    new_content += old_script + "\n</script>\n{% endblock %}"
else:
    new_content += "</script>\n{% endblock %}"

with open('Frontend/templates/unified_offboarding.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("HTML replaced")
