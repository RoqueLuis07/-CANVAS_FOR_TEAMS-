import os

with open('Frontend/templates/unified_offboarding.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update the button
old_btn = '''<button class="btn btn-danger w-100 p-3" id="btnEgresoOneDrive" onclick="openEgresoOneDrive()">
              <i class="bi bi-magic me-2"></i>Pre-visualizar y Ejecutar
            </button>'''
new_btn = '''<button class="btn btn-danger w-100 p-3" id="btnConfirmEgresoOneDrive" onclick="confirmEgresoOneDrive()" disabled>
              <i class="bi bi-check-circle me-1"></i>Confirmar y Procesar
            </button>'''
html = html.replace(old_btn, new_btn)

# 2. Update the select to have onchange
old_select = '''<select class="form-select" id="sheetEgresoOneDrive">'''
new_select = '''<select class="form-select" id="sheetEgresoOneDrive" onchange="openEgresoOneDrive()">'''
html = html.replace(old_select, new_select)

# 3. Insert the Preview Wrap where the modal used to be. (We will replace the modal with the inline wrap)
start_modal = '<!-- Modal Pre-visualización Egreso OneDrive -->'
end_modal = '</div>\n  </div>\n</div>\n'
modal_part = html[html.find(start_modal):html.find(end_modal)+len(end_modal)]

inline_preview = '''<!-- Inline Preview Egreso -->
<div id="egresoPreviewWrap" style="display:none;" class="mb-4">
  <div class="d-flex justify-content-between align-items-center mb-2">
    <label class="form-label fw-semibold mb-0">Previsualización (Muestra)</label>
    <div>
      <span class="badge bg-danger me-2" id="egresoToProcess">0 a procesar</span>
      <span class="badge bg-secondary" id="egresoAlreadyProcessed">0 ignorados</span>
    </div>
  </div>
  <div class="table-responsive border rounded bg-white">
    <table class="table table-sm table-striped mb-0 text-nowrap" id="egresoPreviewTable">
      <thead><tr id="egresoPreviewHeaders"></tr></thead>
      <tbody id="egresoPreviewBody"></tbody>
    </table>
  </div>
</div>
'''
html = html.replace(modal_part, inline_preview)

# 4. Update the JS
# Replace openEgresoOneDrive to not use the modal and enable the button instead
old_js_open = '''            const modal = new bootstrap.Modal(document.getElementById('previewEgresoModal'));
            modal.show();
        } else {'''
new_js_open = '''            document.getElementById('egresoPreviewWrap').style.display = 'block';
            document.getElementById('btnConfirmEgresoOneDrive').disabled = false;
        } else {'''
html = html.replace(old_js_open, new_js_open)

old_js_btn = '''const btn = document.getElementById('btnEgresoOneDrive');'''
new_js_btn = '''const btn = document.getElementById('btnConfirmEgresoOneDrive');
    document.getElementById('egresoPreviewWrap').style.display = 'none';'''
html = html.replace(old_js_btn, new_js_btn)

# Also in confirmEgresoOneDrive, remove the modal.hide()
old_js_confirm = '''            bootstrap.Modal.getInstance(document.getElementById('previewEgresoModal')).hide();'''
new_js_confirm = '''            document.getElementById('egresoPreviewWrap').style.display = 'none';'''
html = html.replace(old_js_confirm, new_js_confirm)

# Fix the formatting of `to_process` badges in JS
old_badge1 = "document.getElementById('egresoToProcess').innerText = data.total_to_process;"
new_badge1 = "document.getElementById('egresoToProcess').innerText = `${data.total_to_process} a procesar`;"
old_badge2 = "document.getElementById('egresoAlreadyProcessed').innerText = data.already_processed;"
new_badge2 = "document.getElementById('egresoAlreadyProcessed').innerText = `${data.already_processed} ignorados`;"
html = html.replace(old_badge1, new_badge1).replace(old_badge2, new_badge2)

with open('Frontend/templates/unified_offboarding.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("unified_offboarding.html refactored")
