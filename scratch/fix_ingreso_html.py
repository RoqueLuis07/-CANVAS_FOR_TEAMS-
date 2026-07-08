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
                    Columnas opcionales: <em>Correo, Usuario, Contraseña, Enviado, ID Curso, ID Equipo</em>.
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

js_code = """
async function fetchDiplomadoSheets() {
    const url = document.getElementById('diplomadoUrl').value;
    const select = document.getElementById('diplomadoSheet');
    const btn = document.getElementById('btnLoadDiplomadoSheets');
    if (!url) return toast('Ingresa la URL primero', 'warning');
    
    const oldText = btn.innerHTML;
    btn.innerHTML = '...';
    btn.disabled = true;
    
    try {
        const sheets = await api.post('/excel/diplomados/sheets', { url: url });
        if (sheets && sheets.length > 0) {
            select.innerHTML = '<option value="">Selecciona una pestaña...</option>';
            sheets.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                select.appendChild(opt);
            });
            toast('Pestañas cargadas', 'success');
        } else {
            select.innerHTML = '<option value="">No se encontraron pestañas</option>';
        }
    } catch (e) {
        toast('Error: ' + e.message, 'danger');
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function previewDiplomados() {
    const url = document.getElementById('diplomadoUrl').value;
    const sheet = document.getElementById('diplomadoSheet').value;
    if (!url || !sheet) return toast('Completa la URL y la pestaña', 'warning');
    
    const btn = document.getElementById('btnPreviewDiplomados');
    setLoading(btn, true);
    
    try {
        const res = await api.post('/excel/diplomados/preview', { url: url, sheet_name: sheet });
        const tbody = document.getElementById('diplomadoPreviewTbody');
        tbody.innerHTML = res.sample.map(r => `
            <tr>
                <td>${r.nombre || '-'}</td>
                <td>${r.cedula || '-'}</td>
            </tr>
        `).join('');
        document.getElementById('diplomadoPreviewWrap').style.display = 'block';
        document.getElementById('btnImportDiplomados').disabled = false;
        toast(`Previsualizando muestra (alumnos a procesar: ${res.students_to_process})`, 'success');
    } catch (e) {
        toast(e.message, 'danger');
    } finally {
        setLoading(btn, false);
    }
}

async function importDiplomados() {
    const url = document.getElementById('diplomadoUrl').value;
    const sheet = document.getElementById('diplomadoSheet').value;
    if (!url || !sheet) return;
    
    if (!confirm('¿Iniciar proceso para Diplomados?')) return;
    
    const btn = document.getElementById('btnImportDiplomados');
    setLoading(btn, true);
    
    try {
        const res = await api.post('/excel/diplomados', { url: url, sheet_name: sheet });
        document.getElementById('diplomadoSuccessCount').innerText = res.succeeded.length;
        document.getElementById('diplomadoErrorCount').innerText = res.failed.length;
        
        document.getElementById('diplomadoSuccessList').innerHTML = res.succeeded.map(r => 
            `<li class="list-group-item py-1 small">
                <strong>${r.nombre}</strong> (${r.login_id})
            </li>`
        ).join('');
        
        document.getElementById('diplomadoErrorList').innerHTML = res.failed.map(r => 
            `<li class="list-group-item py-1 small text-danger">
                ${JSON.stringify(r.input || r)}: ${r.error}
            </li>`
        ).join('');
        
        document.getElementById('diplomadoResultWrap').style.display = 'block';
        toast('Proceso completado', 'success');
    } catch (e) {
        toast(e.message, 'danger');
    } finally {
        setLoading(btn, false);
    }
}

async function fetchMasivoSheets() {
    const url = document.getElementById('masivoUrl').value;
    const select = document.getElementById('masivoSheet');
    const btn = document.getElementById('btnLoadMasivoSheets');
    if (!url) return toast('Ingresa la URL primero', 'warning');
    
    const oldText = btn.innerHTML;
    btn.innerHTML = '...';
    btn.disabled = true;
    
    try {
        const sheets = await api.post('/excel/masivo/sheets', { url: url });
        if (sheets && sheets.length > 0) {
            select.innerHTML = '<option value="">Selecciona una pestaña...</option>';
            sheets.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                select.appendChild(opt);
            });
            toast('Pestañas cargadas', 'success');
        } else {
            select.innerHTML = '<option value="">No se encontraron pestañas</option>';
        }
    } catch (e) {
        toast('Error: ' + e.message, 'danger');
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function previewMasivo() {
    const url = document.getElementById('masivoUrl').value;
    const sheet = document.getElementById('masivoSheet').value;
    if (!url || !sheet) return toast('Completa la URL y la pestaña', 'warning');
    
    const btn = document.getElementById('btnPreviewMasivo');
    setLoading(btn, true);
    
    try {
        const res = await api.post('/excel/masivo/preview', { url: url, sheet_name: sheet });
        const tbody = document.getElementById('masivoPreviewTbody');
        tbody.innerHTML = res.sample.map(r => `
            <tr>
                <td>${r.nombre || '-'}</td>
                <td>${r.cedula || '-'}</td>
            </tr>
        `).join('');
        document.getElementById('masivoPreviewWrap').style.display = 'block';
        document.getElementById('btnImportMasivo').disabled = false;
        toast(`Previsualizando muestra (filas a procesar: ${res.students_to_process})`, 'success');
    } catch (e) {
        toast(e.message, 'danger');
    } finally {
        setLoading(btn, false);
    }
}

async function importMasivo() {
    const url = document.getElementById('masivoUrl').value;
    const sheet = document.getElementById('masivoSheet').value;
    if (!url || !sheet) return;
    
    if (!confirm('¿Iniciar proceso de Carga Masiva?')) return;
    
    const btn = document.getElementById('btnImportMasivo');
    setLoading(btn, true);
    
    try {
        const res = await api.post('/excel/masivo', { url: url, sheet_name: sheet });
        document.getElementById('masivoSuccessCount').innerText = res.succeeded.length;
        document.getElementById('masivoErrorCount').innerText = res.failed.length;
        
        document.getElementById('masivoSuccessList').innerHTML = res.succeeded.map(r => 
            `<li class="list-group-item py-1 small">
                <strong>${r.nombre}</strong> (${r.login_id})
            </li>`
        ).join('');
        
        document.getElementById('masivoErrorList').innerHTML = res.failed.map(r => 
            `<li class="list-group-item py-1 small text-danger">
                ${JSON.stringify(r.input || r)}: ${r.error}
            </li>`
        ).join('');
        
        document.getElementById('masivoResultWrap').style.display = 'block';
        toast('Proceso completado', 'success');
    } catch (e) {
        toast(e.message, 'danger');
    } finally {
        setLoading(btn, false);
    }
}
"""

content = content.replace('<form id="crearIndForm"', diplomados_accordion + "\n" + masivo_accordion + '\n        <form id="crearIndForm"')
content = content.replace('</script>', js_code + '\n</script>')

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("ingreso.html updated successfully!")
