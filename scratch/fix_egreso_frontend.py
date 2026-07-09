import sys
import re

with open('Frontend/templates/unified_offboarding.html', 'r', encoding='utf-8') as f:
    content = f.read()

modal_html = """
<!-- Modal Pre-visualización Egreso OneDrive -->
<div class="modal fade" id="previewEgresoModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header bg-danger text-white">
        <h5 class="modal-title"><i class="bi bi-person-x-fill me-2"></i>Vista Previa: Desvinculación Masiva</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Cerrar"></button>
      </div>
      <div class="modal-body">
        <div class="alert alert-warning mb-3">
          <strong>Aviso:</strong> El sistema procesará a los usuarios que an no tienen un estado de "OK". 
        </div>
        <div class="row text-center mb-3">
          <div class="col-6">
            <h4 class="text-danger mb-0" id="egresoToProcess">0</h4>
            <small class="text-muted">Usuarios por Desvincular</small>
          </div>
          <div class="col-6">
            <h4 class="text-success mb-0" id="egresoAlreadyProcessed">0</h4>
            <small class="text-muted">Ya Procesados (Ignorados)</small>
          </div>
        </div>
        <div class="table-responsive">
          <table class="table table-bordered table-sm fs-7">
            <thead class="table-light" id="egresoPreviewHeaders"></thead>
            <tbody id="egresoPreviewBody"></tbody>
          </table>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
        <button type="button" class="btn btn-danger fw-bold" id="btnConfirmEgresoOneDrive" onclick="confirmEgresoOneDrive()">
          <i class="bi bi-check-circle me-1"></i>Confirmar y Procesar
        </button>
      </div>
    </div>
  </div>
</div>
"""

js_code = """
// --- Egreso Masivo OneDrive ---
async function fetchSheetsEgreso() {
    const url = document.getElementById('urlEgresoOneDrive').value.trim();
    if (!url) return toast("Ingresa el enlace de OneDrive", "warning");

    const btn = document.getElementById('btnLoadSheetsEgreso');
    const select = document.getElementById('sheetEgresoOneDrive');
    
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    btn.disabled = true;

    try {
        const res = await fetch('/excel/egreso/sheets', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url: url })
        });
        
        if (res.ok) {
            const sheets = await res.json();
            select.innerHTML = '';
            sheets.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s; opt.textContent = s;
                select.appendChild(opt);
            });
            toast("Pestañas cargadas", "success");
        } else {
            const err = await res.json();
            toast(err.detail || "Error al cargar pestañas", "danger");
        }
    } catch (e) {
        toast("Error de red", "danger");
    } finally {
        btn.innerHTML = 'Cargar Pestañas';
        btn.disabled = false;
    }
}

async function openEgresoOneDrive() {
    const url = document.getElementById('urlEgresoOneDrive').value.trim();
    const sheet = document.getElementById('sheetEgresoOneDrive').value;
    
    if (!url || !sheet) return toast("Completa el enlace y selecciona la pestaña", "warning");
    
    const btn = document.getElementById('btnEgresoOneDrive');
    const originalBtnHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Cargando...';
    btn.disabled = true;

    try {
        const res = await fetch('/excel/egreso/preview', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url: url, sheet_name: sheet })
        });
        
        if (res.ok) {
            const data = await res.json();
            
            document.getElementById('egresoToProcess').innerText = data.total_to_process;
            document.getElementById('egresoAlreadyProcessed').innerText = data.already_processed;
            
            const thead = document.getElementById('egresoPreviewHeaders');
            thead.innerHTML = '<tr>' + data.headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
            
            const tbody = document.getElementById('egresoPreviewBody');
            tbody.innerHTML = '';
            data.sample_rows.forEach(row => {
                tbody.innerHTML += '<tr>' + row.map(cell => `<td>${cell || ''}</td>`).join('') + '</tr>';
            });
            
            const modal = new bootstrap.Modal(document.getElementById('previewEgresoModal'));
            modal.show();
        } else {
            const err = await res.json();
            toast(err.detail || "Error al generar vista previa", "danger");
        }
    } catch (e) {
        toast("Error de conexión", "danger");
    } finally {
        btn.innerHTML = originalBtnHTML;
        btn.disabled = false;
    }
}

async function confirmEgresoOneDrive() {
    const url = document.getElementById('urlEgresoOneDrive').value.trim();
    const sheet = document.getElementById('sheetEgresoOneDrive').value;
    const deleteAccount = document.getElementById('chkDeleteAccountEgreso').checked;
    
    const btn = document.getElementById('btnConfirmEgresoOneDrive');
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
    btn.disabled = true;

    try {
        const res = await fetch('/excel/egreso/import', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                url: url, 
                sheet_name: sheet,
                delete_account: deleteAccount
            })
        });
        
        if (res.ok) {
            const data = await res.json();
            bootstrap.Modal.getInstance(document.getElementById('previewEgresoModal')).hide();
            toast(`Proceso finalizado. Exitosos: ${data.succeeded.length}, Fallidos: ${data.failed.length}`, "success");
        } else {
            const err = await res.json();
            toast(err.detail || "Error en el procesamiento", "danger");
        }
    } catch (e) {
        toast("Error de conexión al procesar", "danger");
    } finally {
        btn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Confirmar y Procesar';
        btn.disabled = false;
    }
}
"""

if 'id="previewEgresoModal"' not in content:
    content = content.replace('</div>\n\n<script>', f'</div>\n\n{modal_html}\n<script>')
    content = content.replace('</script>', f'{js_code}\n</script>')
    with open('Frontend/templates/unified_offboarding.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Frontend logic injected successfully.")
else:
    print("Frontend logic already exists.")
