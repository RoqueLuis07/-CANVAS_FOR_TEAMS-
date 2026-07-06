import re

html_to_add = """
<!-- Modal Excel Docentes (OneDrive) -->
<div class="modal fade" id="modalExcelDocentes" tabindex="-1">
  <div class="modal-dialog modal-xl">
    <div class="modal-content border-0 shadow-lg">
      <div class="modal-header text-white" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
        <h5 class="modal-title"><i class="bi bi-person-video3 me-2"></i>Alta Docentes (OneDrive)</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body p-4">
        <div class="alert alert-warning mb-4">
          <h6 class="alert-heading fw-bold mb-1"><i class="bi bi-info-circle me-2"></i>Estructura Requerida</h6>
          <p class="mb-0 small">
            El Excel debe estar en OneDrive y tener al menos las columnas: <strong>Nombre</strong> y <strong>Cédula</strong>.<br>
            Columnas opcionales: <em>Correo, Plataforma (both/canvas/teams), ID Curso, ID Equipo</em>.
          </p>
        </div>
        
        <div class="row g-3 mb-4">
          <div class="col-md-8">
            <label class="form-label fw-bold text-secondary">Enlace de Compartir (OneDrive) <span class="text-danger">*</span></label>
            <input type="url" id="doc_url" class="form-control" placeholder="https://usilpy-my.sharepoint.com/:x:/g/personal/..." required>
          </div>
          <div class="col-md-4">
            <label class="form-label fw-bold text-secondary">Nombre de la Pestaña <span class="text-danger">*</span></label>
            <input type="text" id="doc_sheet" class="form-control" placeholder="Ej: Hoja 1" value="Hoja 1" required>
          </div>
        </div>
        
        <div class="d-flex justify-content-end gap-2 mb-4">
          <button type="button" class="btn btn-outline-secondary" onclick="previewDocentes()" id="btnPreviewDocentes">
            <i class="bi bi-eye me-2"></i>Previsualizar
          </button>
          <button type="button" class="btn btn-warning text-dark" onclick="importDocentes()" id="btnImportDocentes" disabled>
            <i class="bi bi-cloud-arrow-up me-2"></i>Procesar Docentes
          </button>
        </div>
        
        <div id="docPreviewWrap" style="display:none;" class="mb-4">
          <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-table me-2"></i>Vista Previa (Muestra)</h6>
          <div class="table-responsive bg-white rounded border">
            <table class="table table-sm table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th>Nombre</th>
                  <th>Cédula</th>
                  <th>Correo</th>
                  <th>Plataforma</th>
                  <th>ID Curso</th>
                  <th>ID Equipo</th>
                </tr>
              </thead>
              <tbody id="docPreviewTbody"></tbody>
            </table>
          </div>
        </div>
        
        <div id="docResultWrap" style="display:none;">
          <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-check-circle me-2"></i>Resultados</h6>
          <div class="row g-3">
            <div class="col-md-6">
              <div class="card border-success h-100">
                <div class="card-header bg-success text-white py-2">
                  <i class="bi bi-check-circle me-2"></i>Éxitos (<span id="docSuccessCount">0</span>)
                </div>
                <div class="card-body p-0">
                  <ul class="list-group list-group-flush" id="docSuccessList" style="max-height: 200px; overflow-y: auto;"></ul>
                </div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="card border-danger h-100">
                <div class="card-header bg-danger text-white py-2">
                  <i class="bi bi-x-circle me-2"></i>Errores (<span id="docErrorCount">0</span>)
                </div>
                <div class="card-body p-0">
                  <ul class="list-group list-group-flush" id="docErrorList" style="max-height: 200px; overflow-y: auto;"></ul>
                </div>
              </div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  </div>
</div>
"""

js_to_add = """
// --- DOCENTES ONEDRIVE ---
let modalDocentes;
function openExcelDocentes() {
    if (!modalDocentes) modalDocentes = new bootstrap.Modal(document.getElementById('modalExcelDocentes'));
    document.getElementById('doc_url').value = '';
    document.getElementById('docPreviewWrap').style.display = 'none';
    document.getElementById('docResultWrap').style.display = 'none';
    document.getElementById('btnImportDocentes').disabled = true;
    modalDocentes.show();
}

async function previewDocentes() {
    const url = document.getElementById('doc_url').value;
    const sheet = document.getElementById('doc_sheet').value;
    if (!url || !sheet) return toast('Completa la URL y la pestaña', 'warning');
    
    const btn = document.getElementById('btnPreviewDocentes');
    setLoading(btn, true);
    
    try {
        const res = await api.post('/excel/docentes-onedrive/preview', { url: url, sheet_name: sheet });
        const tbody = document.getElementById('docPreviewTbody');
        tbody.innerHTML = res.sample.map(r => `
            <tr>
                <td>${r.nombre}</td>
                <td>${r.cedula}</td>
                <td>${r.correo}</td>
                <td><span class="badge bg-secondary">${r.plataforma}</span></td>
                <td>${r.curso || '-'}</td>
                <td>${r.equipo || '-'}</td>
            </tr>
        `).join('');
        document.getElementById('docPreviewWrap').style.display = 'block';
        document.getElementById('btnImportDocentes').disabled = false;
        toast(`Se encontraron ${res.total_rows} filas (previsualizando ${res.valid_rows})`, 'success');
    } catch (e) {
        toast(e.message, 'danger');
    } finally {
        setLoading(btn, false);
    }
}

async function importDocentes() {
    const url = document.getElementById('doc_url').value;
    const sheet = document.getElementById('doc_sheet').value;
    if (!url || !sheet) return;
    
    if (!confirm('¿Iniciar la creación y matriculación de estos docentes?')) return;
    
    const btn = document.getElementById('btnImportDocentes');
    setLoading(btn, true);
    
    try {
        const res = await api.post('/excel/docentes-onedrive', { url: url, sheet_name: sheet });
        document.getElementById('docSuccessCount').innerText = res.succeeded.length;
        document.getElementById('docErrorCount').innerText = res.failed.length;
        
        document.getElementById('docSuccessList').innerHTML = res.succeeded.map(r => 
            `<li class="list-group-item py-1 small">
                <strong>${r.nombre}</strong> (${r.login_id})
                ${r.canvas === 'creado' ? '<span class="badge bg-success ms-1">Canvas</span>' : (r.canvas === 'existía' ? '<span class="badge bg-info ms-1">Canvas (Ya Existía)</span>' : '')}
                ${r.teams === 'creado' ? '<span class="badge bg-primary ms-1">Teams</span>' : (r.teams === 'existía' ? '<span class="badge bg-info ms-1">Teams (Ya Existía)</span>' : '')}
                ${r.canvas_enroll === 'teacher' ? '<span class="badge bg-success ms-1">Enroll Curso</span>' : ''}
                ${r.teams_enroll === 'owner' ? '<span class="badge bg-primary ms-1">Enroll Equipo</span>' : ''}
            </li>`
        ).join('');
        
        document.getElementById('docErrorList').innerHTML = res.failed.map(r => 
            `<li class="list-group-item py-1 small text-danger">
                <strong>${r.correo}</strong>: ${r.error}
            </li>`
        ).join('');
        
        document.getElementById('docResultWrap').style.display = 'block';
        toast('Proceso completado', 'success');
    } catch (e) {
        toast(e.message, 'danger');
    } finally {
        setLoading(btn, false);
    }
}
"""

with open(r"Frontend\templates\ingreso.html", "r", encoding="utf-8") as f:
    content = f.read()

if "<!-- Modal Excel Diplomados -->" in content:
    content = content.replace("<!-- Modal Excel Diplomados -->", html_to_add + "\n<!-- Modal Excel Diplomados -->")
else:
    content = content.replace("<script>", html_to_add + "\n<script>", 1)

content = content.replace("</script>\n{% endblock %}", js_to_add + "\n</script>\n{% endblock %}")

with open(r"Frontend\templates\ingreso.html", "w", encoding="utf-8") as f:
    f.write(content)
