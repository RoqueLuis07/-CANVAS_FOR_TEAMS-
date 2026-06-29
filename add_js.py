import os

JS_CODE = '''

/* ?? Excel Upload that returns a blob (download modified excel) */
async function uploadExcelDownloadBlob(url, fileInputId) {
  const inp = document.getElementById(fileInputId);
  if (!inp.files[0]) throw new Error('Selecciona un archivo Excel primero');
  const fd = new FormData();
  fd.append('file', inp.files[0]);
  
  const originalName = inp.files[0].name;
  const newName = originalName.replace(".xlsx", "_procesado.xlsx");

  const r = await fetch(url, { method: 'POST', body: fd });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(e.detail || r.statusText);
  }
  
  const blob = await r.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = newName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

/* ?? Modal function for Diplomados */
function openExcelDiplomados() {
  document.getElementById('globalModalTitle').innerHTML = '<i class="bi bi-file-earmark-excel me-2"></i>Carga de Diplomados (Excel)';
  document.getElementById('globalModalBody').innerHTML = \
    <div class="alert alert-info">
      Sube aquí tu planilla original de Diplomados de OneDrive. El sistema leerá las columnas <b>Nombre, Cedula y Correo</b>, y te devolverá el archivo idéntico pero con las columnas <b>Usuario, Contraseña y Enviado</b> completadas.
    </div>
    <div class="row">
      <div class="col-md-6 offset-md-3">
        <div class="drop-zone text-center p-5 border rounded bg-light" id="dz_diplomado" style="cursor: pointer;">
          <i class="bi bi-cloud-arrow-up display-4 text-secondary mb-3"></i><br>
          Haz clic o arrastra tu Excel aquí
        </div>
        <input type="file" id="excelFileDiplomado" accept=".xlsx,.xls" class="d-none">
        <div id="previewAreaDiplomado" class="mt-3 text-center text-muted small"></div>
      </div>
    </div>
  \;
  document.getElementById('globalModalFooter').innerHTML = \
    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>
    <button type="button" class="btn btn-success" id="btnUploadDiplomado" onclick="doUploadDiplomados()"><i class="bi bi-play-circle me-1"></i>Procesar Planilla</button>
  \;
  
  new bootstrap.Modal(document.getElementById('globalModal')).show();
  
  // init dropzone after small delay for DOM
  setTimeout(() => {
    initDropZone('dz_diplomado', 'excelFileDiplomado', file => {
      document.getElementById('previewAreaDiplomado').innerHTML = \<i class="bi bi-file-earmark-check text-success me-1"></i> Archivo seleccionado: <b>\</b>\;
    });
  }, 100);
}

function doUploadDiplomados() {
  const btn = document.getElementById('btnUploadDiplomado');
  setLoading(btn, true);
  toast("Procesando usuarios, esto puede tardar unos minutos...", "info");
  
  uploadExcelDownloadBlob('/excel/diplomados', 'excelFileDiplomado')
    .then(() => {
      toast('¡Planilla procesada con éxito! Revisa tus descargas.', 'success');
      bootstrap.Modal.getInstance(document.getElementById('globalModal')).hide();
    })
    .catch(e => {
      toast('Error: ' + e.message, 'danger');
    })
    .finally(() => setLoading(btn, false));
}
'''

with open("Frontend/static/js/main.js", "a", encoding="utf-8") as f:
    f.write(JS_CODE)
