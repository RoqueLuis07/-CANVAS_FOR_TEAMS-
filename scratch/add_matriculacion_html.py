import re

with open('Frontend/templates/unified_enrollments.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the top button
btn_individual = '<button class="btn btn-info text-dark" data-bs-toggle="collapse" data-bs-target="#collapseMatriculacionInd" aria-expanded="false" aria-controls="collapseMatriculacionInd"><i class="bi bi-person-check-fill me-2"></i>Matriculación Individual</button>'
content = content.replace('<a href="/excel/template/unified-enrollment"', btn_individual + '\n    <a href="/excel/template/unified-enrollment"')

# 2. Add the Accordion HTML
accordion_html = """
<!-- Accordion Matriculación Individual -->
<div class="accordion mb-4" id="accordionMatriculacionInd">
  <div class="accordion-item border-info shadow-sm">
    <h2 class="accordion-header" id="headingMatriculacionInd">
      <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseMatriculacionInd" aria-expanded="false" aria-controls="collapseMatriculacionInd" style="background: linear-gradient(135deg, rgba(13, 202, 240, 0.1), rgba(13, 202, 240, 0.05));">
        <i class="bi bi-person-check-fill me-2 text-info"></i> Matriculación Individual
      </button>
    </h2>
    <div id="collapseMatriculacionInd" class="accordion-collapse collapse" aria-labelledby="headingMatriculacionInd" data-bs-parent="#accordionMatriculacionInd">
      <div class="accordion-body p-4">
        
        <div class="row g-3 mb-4">
            <div class="col-md-6">
                <label class="form-label fw-semibold">Correo Institucional <span class="text-danger">*</span></label>
                <div class="input-group">
                    <span class="input-group-text bg-white"><i class="bi bi-envelope"></i></span>
                    <input type="email" id="mi_correo" class="form-control" placeholder="ejemplo@usil.edu.py" required>
                </div>
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold">SYS (Cédula o SIS) <span class="text-danger">*</span></label>
                <div class="input-group">
                    <span class="input-group-text bg-white"><i class="bi bi-card-heading"></i></span>
                    <input type="text" id="mi_sys" class="form-control" placeholder="Ej: 1234567" required>
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <label class="form-label fw-semibold">Programa <span class="text-danger">*</span></label>
                <select id="mi_programa" class="form-select" onchange="mi_onProgramChange()" required>
                    <option value="" disabled selected>Seleccione el programa...</option>
                    <option value="GA">GA</option>
                    <option value="GND">GND</option>
                    <option value="CPEL">CPEL</option>
                </select>
            </div>
            <div class="col-md-8 position-relative">
                <label class="form-label fw-semibold">Materias (Buscador) <span class="text-danger">*</span></label>
                <div class="input-group">
                    <span class="input-group-text bg-white"><i class="bi bi-search"></i></span>
                    <input type="text" id="mi_search" class="form-control" placeholder="Buscar materia por nombre o ID..." disabled oninput="mi_onSearchInput()">
                </div>
                <!-- Autocomplete dropdown -->
                <ul id="mi_autocomplete_list" class="list-group position-absolute w-100 shadow-sm" style="z-index: 1000; display: none; max-height: 200px; overflow-y: auto;">
                </ul>
            </div>
        </div>

        <div class="mb-4">
            <label class="form-label fw-semibold">Materias Seleccionadas</label>
            <div id="mi_selected_materias" class="border rounded p-3 bg-light" style="min-height: 100px;">
                <p class="text-muted small mb-0 fst-italic" id="mi_empty_msg">No hay materias seleccionadas. Busca y selecciona en el recuadro superior.</p>
                <div id="mi_tags_container" class="d-flex flex-wrap gap-2"></div>
            </div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-md-6">
                <label class="form-label fw-semibold">Plataforma</label>
                <select id="mi_plataforma" class="form-select">
                    <option value="both" selected>Ambas (Canvas + Teams)</option>
                    <option value="canvas">Solo Canvas</option>
                    <option value="teams">Solo Teams</option>
                </select>
            </div>
        </div>

        <div id="mi_resultWrap" style="display:none;" class="alert alert-info mb-4"></div>

        <div class="d-flex justify-content-end gap-2 border-top pt-3">
            <button type="button" class="btn btn-outline-secondary" onclick="mi_resetForm()">Limpiar</button>
            <button type="button" class="btn btn-info px-4 text-dark fw-bold" id="btnMatriculacionInd" onclick="mi_doEnroll()">
                <i class="bi bi-lightning-charge-fill me-1"></i> Ejecutar matriculación
            </button>
        </div>
        
        <hr class="my-5">
        
        <h5 class="fw-bold mb-3"><i class="bi bi-clock-history me-2"></i>Historial Reciente</h5>
        <div class="table-responsive bg-white border rounded">
            <table class="table table-sm table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Fecha</th>
                        <th>Correo / SYS</th>
                        <th>Programa</th>
                        <th>Materias Procesadas</th>
                        <th>Estado Canvas</th>
                        <th>Estado Teams</th>
                    </tr>
                </thead>
                <tbody id="mi_history_body">
                    <tr><td colspan="6" class="text-center text-muted py-3">No hay registros recientes</td></tr>
                </tbody>
            </table>
        </div>

      </div>
    </div>
  </div>
</div>
"""
content = content.replace('<!-- Accordion Matriculación Masiva (OneDrive) -->', accordion_html + '\n<!-- Accordion Matriculación Masiva (OneDrive) -->')

with open('Frontend/templates/unified_enrollments.html', 'w', encoding='utf-8') as f:
    f.write(content)
