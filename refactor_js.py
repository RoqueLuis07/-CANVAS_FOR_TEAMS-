import sys

with open('Frontend/static/js/main.js', 'r', encoding='utf-8') as f:
    content = f.read()

new_code = '''
// --- EGRESO MASIVO (ONEDRIVE) ---

async function openEgresoOneDrive() {
  const btn = document.getElementById('btnEgresoOneDrive');
  const urlInput = document.getElementById('urlEgresoOneDrive').value.trim();
  const sheetInput = document.getElementById('sheetEgresoOneDrive').value.trim();

  if (!urlInput || !sheetInput) {
    toast("Por favor ingresa la URL de OneDrive y el nombre de la pestaña.", "warning");
    return;
  }

  setLoading(btn, true);
  toast("Analizando el archivo para pre-visualizar...", "info");
  
  try {
    const previewRes = await api.post('/excel/egreso/preview', { url: urlInput, sheet_name: sheetInput });
    
    // We reuse the global modal for the preview
    const m = new bootstrap.Modal(document.getElementById('globalModal'));
    m.show();
    
    if (previewRes.students_to_process === 0) {
        toast("No hay ningún alumno por dar de baja en esta pestaña (todos tienen la columna Desvinculado llena).", "warning");
        setLoading(btn, false);
        return;
    }

    let tableHtml = `<div class="table-responsive mt-3" style="max-height: 300px; overflow-y: auto;">
      <table class="table table-sm table-bordered table-striped table-hover">
        <thead class="table-light" style="position: sticky; top: 0; z-index: 1;">
          <tr>
            <th class="text-center" style="width: 50px;">Nº</th>
            <th>Nombre Detectado</th>
            <th>Cédula / ID</th>
          </tr>
        </thead>
        <tbody>`;
    
    if (previewRes.student_details) {
        previewRes.student_details.forEach((s, idx) => {
            tableHtml += `<tr>
                <td class="text-center">${idx + 1}</td>
                <td>${s.nombre}</td>
                <td><span class="badge bg-danger">${s.cedula}</span></td>
            </tr>`;
        });
    }
    tableHtml += `</tbody></table></div>`;

    document.getElementById('globalModalTitle').innerHTML = '<i class="bi bi-person-x-fill me-2"></i>Pre-visualización de Bajas';
    document.getElementById('globalModalBody').innerHTML = `
      <div class="alert alert-danger mb-0">
        <strong>Peligro: Revisa los datos cuidadosamente.</strong><br>
        Se van a dar de baja <b>${previewRes.students_to_process}</b> alumnos.<br>
        <small class="text-muted">Alumnos ignorados (ya desvinculados previamente): ${previewRes.students_already_processed}</small>
      </div>
      ${tableHtml}
    `;
    
    const safeUrl = urlInput.replace(/'/g, "\\\\'");
    const safeSheet = sheetInput.replace(/'/g, "\\\\'");

    document.getElementById('globalModalFooter').innerHTML = `
      <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>
      <button type="button" class="btn btn-danger" id="btnConfirmEgreso" onclick="executeEgresoOneDrive('${safeUrl}', '${safeSheet}')">
        <i class="bi bi-trash-fill me-1"></i>Confirmar Desvinculación Masiva
      </button>
    `;

  } catch (e) {
    toast('Error: ' + (e.detail || e.message || e), 'danger');
  } finally {
    setLoading(btn, false);
  }
}

async function executeEgresoOneDrive(urlInput, sheetInput) {
    const btn = document.getElementById('btnConfirmEgreso');
    setLoading(btn, true);
    toast("Iniciando desvinculación masiva... observa tu Excel abierto.", "info");
    
    try {
        const res = await api.post('/excel/egreso', { url: urlInput, sheet_name: sheetInput });
        toast(`Operación exitosa. ${res.succeeded?.length || 0} alumnos dados de baja.`, 'success');
        bootstrap.Modal.getInstance(document.getElementById('globalModal')).hide();
    } catch (e) {
        toast('Error: ' + (e.detail || e.message || e), 'danger');
    } finally {
        setLoading(btn, false);
    }
}
'''

content += "\n" + new_code

with open('Frontend/static/js/main.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("JS appended")
