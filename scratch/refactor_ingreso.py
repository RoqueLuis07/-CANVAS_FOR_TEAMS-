import os

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    html = f.read()

# HTML Replacements
def get_new_preview_wrap(prefix, title="Previsualización (Muestra)"):
    return f'''<div id="{prefix}PreviewWrap" style="display:none;" class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <label class="form-label fw-semibold mb-0"><i class="bi bi-table me-2"></i>{title}</label>
                      <div>
                        <span class="badge bg-danger me-2" id="{prefix}PreviewToProcess">0 a procesar</span>
                        <span class="badge bg-secondary" id="{prefix}PreviewSkipped">0 ignorados</span>
                      </div>
                    </div>
                    <div class="table-responsive border rounded bg-white">
                      <table class="table table-sm table-striped mb-0 text-nowrap" id="{prefix}PreviewTable">
                        <thead class="table-light" id="{prefix}PreviewThead"></thead>
                        <tbody id="{prefix}PreviewTbody"></tbody>
                      </table>
                    </div>
                  </div>'''

old_masivo_wrap = '''                  <div id="masivoPreviewWrap" style="display:none;" class="mb-4">
                    <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-table me-2"></i>Vista Previa (Muestra)</h6>
                    <div class="table-responsive bg-white rounded border">
                      <table class="table table-sm table-hover mb-0">
                        <thead class="table-light" id="masivoPreviewThead">
                          <tr>
                            <th>Nombre</th>
                            <th>Cédula</th>
                          </tr>
                        </thead>
                        <tbody id="masivoPreviewTbody"></tbody>
                      </table>
                    </div>
                  </div>'''
html = html.replace(old_masivo_wrap.replace('Cédula', 'CǸdula'), get_new_preview_wrap('masivo'))

old_diplomado_wrap = '''                  <div id="diplomadoPreviewWrap" style="display:none;" class="mb-4">
                    <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-table me-2"></i>Vista Previa (Muestra)</h6>
                    <div class="table-responsive bg-white rounded border">
                      <table class="table table-sm table-hover mb-0">
                          <thead class="table-light" id="diplomadoPreviewThead">
                            <tr>
                              <th>Nombre</th>
                              <th>Cédula</th>
                            </tr>
                          </thead>
                        <tbody id="diplomadoPreviewTbody"></tbody>
                      </table>
                    </div>
                  </div>'''
html = html.replace(old_diplomado_wrap.replace('Cédula', 'CǸdula'), get_new_preview_wrap('diplomado'))

old_doc_wrap = '''                  <div id="docPreviewWrap" style="display:none;" class="mb-4">
                    <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-table me-2"></i>Vista Previa (Muestra)</h6>
                    <div class="table-responsive bg-white rounded border">
                      <table class="table table-sm table-hover mb-0">
                        <thead class="table-light" id="docPreviewThead">
                          <tr>
                            <th>Nombre</th>
                            <th>Cédula</th>
                          </tr>
                        </thead>
                        <tbody id="docPreviewTbody"></tbody>
                      </table>
                    </div>
                  </div>'''
html = html.replace(old_doc_wrap.replace('Cédula', 'CǸdula'), get_new_preview_wrap('doc'))

# Removing the old "Previsualizar" buttons from UI since they are redundant (onchange already calls them)
old_masivo_btns = '''                  <div class="d-flex justify-content-end gap-2 mb-4">
                    <button type="button" class="btn btn-outline-secondary d-none" onclick="previewMasivo()" id="btnPreviewMasivo">
                      <i class="bi bi-eye me-2"></i>Previsualizar
                    </button>
                    <button type="button" class="btn btn-primary" onclick="importMasivo()" id="btnImportMasivo" disabled>
                      <i class="bi bi-cloud-arrow-up me-2"></i>Procesar Masiva
                    </button>
                  </div>'''
new_masivo_btns = '''                  <div class="d-flex justify-content-end mb-4">
                    <button type="button" class="btn btn-primary" onclick="importMasivo()" id="btnImportMasivo" disabled>
                      <i class="bi bi-check-circle me-2"></i>Confirmar y Procesar
                    </button>
                  </div>'''
html = html.replace(old_masivo_btns, new_masivo_btns)

old_diplomado_btns = '''                  <div class="d-flex justify-content-end gap-2 mb-4">
                    <button type="button" class="btn btn-outline-secondary d-none" onclick="previewDiplomados()" id="btnPreviewDiplomados">
                      <i class="bi bi-eye me-2"></i>Previsualizar
                    </button>
                    <button type="button" class="btn btn-success text-white" onclick="importDiplomados()" id="btnImportDiplomados" disabled>
                      <i class="bi bi-cloud-arrow-up me-2"></i>Procesar Diplomados
                    </button>
                  </div>'''
new_diplomado_btns = '''                  <div class="d-flex justify-content-end mb-4">
                    <button type="button" class="btn btn-success text-white" onclick="importDiplomados()" id="btnImportDiplomados" disabled>
                      <i class="bi bi-check-circle me-2"></i>Confirmar y Procesar
                    </button>
                  </div>'''
html = html.replace(old_diplomado_btns, new_diplomado_btns)

old_doc_btns = '''                  <div class="d-flex justify-content-end gap-2 mb-4">
                    <button type="button" class="btn btn-outline-secondary d-none" onclick="previewDocentes()" id="btnPreviewDocentes">
                      <i class="bi bi-eye me-2"></i>Previsualizar
                    </button>
                    <button type="button" class="btn btn-warning text-dark fw-bold" onclick="importDocentes()" id="btnImportDocentes" disabled>
                      <i class="bi bi-cloud-arrow-up me-2"></i>Procesar Docentes
                    </button>
                  </div>'''
new_doc_btns = '''                  <div class="d-flex justify-content-end mb-4">
                    <button type="button" class="btn btn-warning text-dark fw-bold" onclick="importDocentes()" id="btnImportDocentes" disabled>
                      <i class="bi bi-check-circle me-2"></i>Confirmar y Procesar
                    </button>
                  </div>'''
html = html.replace(old_doc_btns, new_doc_btns)


# JS Logic Replacement
def get_new_js_preview(prefix, btn_id):
    return f'''
          const thead = document.getElementById('{prefix}PreviewThead');
          const tbody = document.getElementById('{prefix}PreviewTbody');
          
          document.getElementById('{prefix}PreviewToProcess').innerText = `${{res.students_to_process}} a procesar`;
          document.getElementById('{prefix}PreviewSkipped').innerText = `${{res.students_already_processed}} ignorados`;
          
          thead.innerHTML = `<tr>${{res.headers.map(h => `<th>${{h}}</th>`).join('')}}</tr>`;
          
          let bodyHTML = '';
          res.sample_rows.forEach(r => {{
              let rowHtml = '';
              res.headers.forEach(h => {{
                  let cellVal = r[h] || '';
                  if (h.toLowerCase().includes('estado') || h.toLowerCase().includes('enviado')) {{
                      if (cellVal.toLowerCase() === 'ok' || cellVal.toLowerCase().includes('matriculado')) {{
                          cellVal = `<span class="badge bg-warning text-dark">${{cellVal}}</span>`;
                      }} else if (cellVal.toLowerCase().includes('error')) {{
                          cellVal = `<span class="badge bg-danger">${{cellVal}}</span><span class="badge bg-success ms-1">Reintento</span>`;
                      }} else {{
                          cellVal = `<span class="badge bg-success">A procesar</span>`;
                      }}
                  }}
                  rowHtml += `<td>${{cellVal}}</td>`;
              }});
              bodyHTML += `<tr>${{rowHtml}}</tr>`;
          }});
          tbody.innerHTML = bodyHTML;
          document.getElementById('{prefix}PreviewWrap').style.display = 'block';
          document.getElementById('{btn_id}').disabled = false;
          // toast(`Previsualizando muestra`, 'success');
'''

# Replace for Masivo
old_masivo_js = '''          const thead = document.getElementById('masivoPreviewThead');
          const tbody = document.getElementById('masivoPreviewTbody');
          
          thead.innerHTML = `<tr>${res.headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
          
          tbody.innerHTML = res.sample_rows.map(r => {
              return `<tr>${res.headers.map(h => `<td>${r[h] || '-'}</td>`).join('')}</tr>`;
          }).join('');
          document.getElementById('masivoPreviewWrap').style.display = 'block';
          document.getElementById('btnImportMasivo').disabled = false;
          toast(`Previsualizando muestra (filas a procesar: ${res.students_to_process})`, 'success');'''
html = html.replace(old_masivo_js, get_new_js_preview('masivo', 'btnImportMasivo'))

# Replace for Diplomados
old_diplomado_js = '''          const thead = document.getElementById('diplomadoPreviewThead');
          const tbody = document.getElementById('diplomadoPreviewTbody');
          
          thead.innerHTML = `<tr>${res.headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
          
          tbody.innerHTML = res.sample_rows.map(r => {
              return `<tr>${res.headers.map(h => `<td>${r[h] || '-'}</td>`).join('')}</tr>`;
          }).join('');
          document.getElementById('diplomadoPreviewWrap').style.display = 'block';
          document.getElementById('btnImportDiplomados').disabled = false;
          toast(`Previsualizando muestra (alumnos a procesar: ${res.students_to_process})`, 'success');'''
html = html.replace(old_diplomado_js, get_new_js_preview('diplomado', 'btnImportDiplomados'))

# Replace for Docentes
old_docentes_js = '''          const thead = document.getElementById('docPreviewThead');
          const tbody = document.getElementById('docPreviewTbody');
          
          thead.innerHTML = `<tr>${res.headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
          
          tbody.innerHTML = res.sample_rows.map(r => {
              return `<tr>${res.headers.map(h => `<td>${r[h] || '-'}</td>`).join('')}</tr>`;
          }).join('');
          document.getElementById('docPreviewWrap').style.display = 'block';
          document.getElementById('btnImportDocentes').disabled = false;
          toast(`Previsualizando muestra (docentes a procesar: ${res.docentes_to_process})`, 'success');'''

new_docentes_js = get_new_js_preview('doc', 'btnImportDocentes').replace('res.students_to_process', 'res.docentes_to_process').replace('res.students_already_processed', 'res.docentes_already_processed')
html = html.replace(old_docentes_js, new_docentes_js)

# Also fix the `btn` being grabbed for setLoading since we removed the preview buttons!
html = html.replace("const btn = document.getElementById('btnPreviewMasivo');", "const btn = document.getElementById('btnImportMasivo'); btn.innerHTML = '<span class=\"spinner-border spinner-border-sm me-2\"></span>Cargando...';")
html = html.replace("const btn = document.getElementById('btnPreviewDiplomados');", "const btn = document.getElementById('btnImportDiplomados'); btn.innerHTML = '<span class=\"spinner-border spinner-border-sm me-2\"></span>Cargando...';")
html = html.replace("const btn = document.getElementById('btnPreviewDocentes');", "const btn = document.getElementById('btnImportDocentes'); btn.innerHTML = '<span class=\"spinner-border spinner-border-sm me-2\"></span>Cargando...';")

# We must restore the button texts in finally{}
html = html.replace("          setLoading(btn, false);\n      }\n  }\n  \n  async function importMasivo", "          btn.innerHTML = '<i class=\"bi bi-check-circle me-2\"></i>Confirmar y Procesar';\n      }\n  }\n  \n  async function importMasivo")
html = html.replace("          setLoading(btn, false);\n      }\n  }\n  \n  async function importDiplomados", "          btn.innerHTML = '<i class=\"bi bi-check-circle me-2\"></i>Confirmar y Procesar';\n      }\n  }\n  \n  async function importDiplomados")
html = html.replace("          setLoading(btn, false);\n      }\n  }\n  \n  async function importDocentes", "          btn.innerHTML = '<i class=\"bi bi-check-circle me-2\"></i>Confirmar y Procesar';\n      }\n  }\n  \n  async function importDocentes")


with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("ingreso.html refactored")
