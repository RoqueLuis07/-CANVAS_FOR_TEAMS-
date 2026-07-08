import re
import os

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update buttons
content = content.replace(
    '<button class="btn btn-success me-2" onclick="openExcelDiplomados()"><i class="bi bi-file-earmark-excel me-2"></i>Carga Diplomados</button>',
    '<button class="btn btn-success me-2" data-bs-toggle="collapse" data-bs-target="#collapseDiplomados" aria-expanded="false" aria-controls="collapseDiplomados"><i class="bi bi-file-earmark-excel me-2"></i>Carga Diplomados</button>'
)

content = content.replace(
    '<button class="btn btn-primary" onclick="openExcelMasivo()"><i class="bi bi-people-fill me-2"></i>Carga Masiva</button>',
    '<button class="btn btn-primary" data-bs-toggle="collapse" data-bs-target="#collapseMasivo" aria-expanded="false" aria-controls="collapseMasivo"><i class="bi bi-people-fill me-2"></i>Carga Masiva</button>'
)

# 2. Add new accordions
diplomados_accordion = """
        <!-- Accordion Diplomados (OneDrive) -->
        <div class="accordion mb-4" id="accordionDiplomados">
          <div class="accordion-item border-success shadow-sm">
            <h2 class="accordion-header" id="headingDiplomados">
              <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseDiplomados" aria-expanded="false" aria-controls="collapseDiplomados" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));">
                <i class="bi bi-file-earmark-excel me-2 text-success"></i> Carga Diplomados (OneDrive)
              </button>
            </h2>
            <div id="collapseDiplomados" class="accordion-collapse collapse" aria-labelledby="headingDiplomados" data-bs-parent="#accordionDiplomados">
              <div class="accordion-body p-4">
                <div class="alert alert-success mb-4">
                  <h6 class="alert-heading fw-bold mb-1"><i class="bi bi-info-circle me-2"></i>Estructura Requerida</h6>
                  <p class="mb-0 small">
                    El Excel debe estar en OneDrive y tener al menos las columnas: <strong>Nombre</strong> y <strong>Cédula</strong>.<br>
                    Columnas opcionales: <em>Correo, Usuario (Auto), Contraseña (Auto), Enviado (Auto), ID Curso, ID Equipo</em>.
                  </p>
                </div>
                
                <div class="row g-3 mb-4">
                  <div class="col-md-8">
                    <label class="form-label fw-bold text-secondary">Enlace de Compartir (OneDrive) <span class="text-danger">*</span></label>
                    <div class="input-group">
                      <input type="url" id="diplomadoUrl" class="form-control" placeholder="https://usilpy-my.sharepoint.com/:x:/g/personal/..." required>
                      <button class="btn btn-success text-white fw-bold" type="button" id="btnLoadDiplomadoSheets" onclick="fetchDiplomadoSheets()"><i class="bi bi-cloud-arrow-down me-1"></i>Cargar Pestañas</button>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <label class="form-label fw-bold text-secondary">Seleccionar Pestaña <span class="text-danger">*</span></label>
                    <select id="diplomadoSheet" class="form-select" required>
                      <option value="">Carga las pestañas primero...</option>
                    </select>
                  </div>
                </div>
                
                <div class="d-flex justify-content-end gap-2 mb-4">
                  <button type="button" class="btn btn-outline-secondary" onclick="previewDiplomados()" id="btnPreviewDiplomados">
                    <i class="bi bi-eye me-2"></i>Previsualizar
                  </button>
                  <button type="button" class="btn btn-success text-white" onclick="importDiplomados()" id="btnImportDiplomados" disabled>
                    <i class="bi bi-cloud-arrow-up me-2"></i>Procesar Diplomados
                  </button>
                </div>
                
                <div id="diplomadoPreviewWrap" style="display:none;" class="mb-4">
                  <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-table me-2"></i>Vista Previa (Muestra)</h6>
                  <div class="table-responsive bg-white rounded border">
                    <table class="table table-sm table-hover mb-0">
                      <thead class="table-light">
                        <tr>
                          <th>Nombre</th>
                          <th>Cédula</th>
                        </tr>
                      </thead>
                      <tbody id="diplomadoPreviewTbody"></tbody>
                    </table>
                  </div>
                </div>
                
                <div id="diplomadoResultWrap" style="display:none;">
                  <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-check-circle me-2"></i>Resultados del Proceso</h6>
                  <div class="row">
                    <div class="col-md-6">
                      <div class="card border-success h-100">
                        <div class="card-header bg-success text-white fw-bold py-2"><i class="bi bi-check2-all me-1"></i>Éxitos (<span id="diplomadoSuccessCount">0</span>)</div>
                        <ul class="list-group list-group-flush" id="diplomadoSuccessList" style="max-height: 250px; overflow-y:auto;"></ul>
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="card border-danger h-100 mt-3 mt-md-0">
                        <div class="card-header bg-danger text-white fw-bold py-2"><i class="bi bi-exclamation-triangle me-1"></i>Errores (<span id="diplomadoErrorCount">0</span>)</div>
                        <ul class="list-group list-group-flush" id="diplomadoErrorList" style="max-height: 250px; overflow-y:auto;"></ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
"""

masivo_accordion = """
        <!-- Accordion Masivo (OneDrive) -->
        <div class="accordion mb-4" id="accordionMasivo">
          <div class="accordion-item border-primary shadow-sm">
            <h2 class="accordion-header" id="headingMasivo">
              <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseMasivo" aria-expanded="false" aria-controls="collapseMasivo" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1));">
                <i class="bi bi-people-fill me-2 text-primary"></i> Carga Masiva (OneDrive)
              </button>
            </h2>
            <div id="collapseMasivo" class="accordion-collapse collapse" aria-labelledby="headingMasivo" data-bs-parent="#accordionMasivo">
              <div class="accordion-body p-4">
                <div class="alert alert-primary mb-4">
                  <h6 class="alert-heading fw-bold mb-1"><i class="bi bi-info-circle me-2"></i>Estructura Requerida</h6>
                  <p class="mb-0 small">
                    El Excel debe estar en OneDrive y tener al menos las columnas: <strong>Nombre</strong> y <strong>Cédula</strong>.<br>
                    Columnas opcionales: <em>Correo, Plataforma, Rol, ID Curso, ID Equipo, etc.</em>
                  </p>
                </div>
                
                <div class="row g-3 mb-4">
                  <div class="col-md-8">
                    <label class="form-label fw-bold text-secondary">Enlace de Compartir (OneDrive) <span class="text-danger">*</span></label>
                    <div class="input-group">
                      <input type="url" id="masivoUrl" class="form-control" placeholder="https://usilpy-my.sharepoint.com/:x:/g/personal/..." required>
                      <button class="btn btn-primary fw-bold" type="button" id="btnLoadMasivoSheets" onclick="fetchMasivoSheets()"><i class="bi bi-cloud-arrow-down me-1"></i>Cargar Pestañas</button>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <label class="form-label fw-bold text-secondary">Seleccionar Pestaña <span class="text-danger">*</span></label>
                    <select id="masivoSheet" class="form-select" required>
                      <option value="">Carga las pestañas primero...</option>
                    </select>
                  </div>
                </div>
                
                <div class="d-flex justify-content-end gap-2 mb-4">
                  <button type="button" class="btn btn-outline-secondary" onclick="previewMasivo()" id="btnPreviewMasivo">
                    <i class="bi bi-eye me-2"></i>Previsualizar
                  </button>
                  <button type="button" class="btn btn-primary" onclick="importMasivo()" id="btnImportMasivo" disabled>
                    <i class="bi bi-cloud-arrow-up me-2"></i>Procesar Masiva
                  </button>
                </div>
                
                <div id="masivoPreviewWrap" style="display:none;" class="mb-4">
                  <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-table me-2"></i>Vista Previa (Muestra)</h6>
                  <div class="table-responsive bg-white rounded border">
                    <table class="table table-sm table-hover mb-0">
                      <thead class="table-light">
                        <tr>
                          <th>Nombre</th>
                          <th>Cédula</th>
                        </tr>
                      </thead>
                      <tbody id="masivoPreviewTbody"></tbody>
                    </table>
                  </div>
                </div>
                
                <div id="masivoResultWrap" style="display:none;">
                  <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-check-circle me-2"></i>Resultados del Proceso</h6>
                  <div class="row">
                    <div class="col-md-6">
                      <div class="card border-success h-100">
                        <div class="card-header bg-success text-white fw-bold py-2"><i class="bi bi-check2-all me-1"></i>Éxitos (<span id="masivoSuccessCount">0</span>)</div>
                        <ul class="list-group list-group-flush" id="masivoSuccessList" style="max-height: 250px; overflow-y:auto;"></ul>
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="card border-danger h-100 mt-3 mt-md-0">
                        <div class="card-header bg-danger text-white fw-bold py-2"><i class="bi bi-exclamation-triangle me-1"></i>Errores (<span id="masivoErrorCount">0</span>)</div>
                        <ul class="list-group list-group-flush" id="masivoErrorList" style="max-height: 250px; overflow-y:auto;"></ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
"""

# Find the end of accordionDocentes
end_docentes_idx = content.find('<!-- Fin Docentes -->') # wait, there's no such comment.
# Let's just insert it before "</div> <!-- End CREAR USUARIO -->" which is `</div>` right after `accordionDocentes` probably.
# Looking at the HTML, it's after `</div> <!-- /tab-pane #crear -->`
# Let's just search for the end of accordionDocentes div. 
match = re.search(r'(<div id="docResultWrap".*?</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*</div>)', content, re.DOTALL)
if match:
    content = content[:match.end()] + "\n" + diplomados_accordion + "\n" + masivo_accordion + "\n" + content[match.end():]
else:
    print("Could not find insertion point!")

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML structure updated!")
