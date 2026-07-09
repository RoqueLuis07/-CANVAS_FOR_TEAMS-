import os

with open('Frontend/templates/canvas/courses.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update the sheet dropdown to have onchange
old_select = '''<select class="form-select" id="coursesOdSheet">'''
new_select = '''<select class="form-select" id="coursesOdSheet" onchange="doPreviewCourses()">'''
html = html.replace(old_select, new_select)

# 2. Remove the "Pre-visualizar" button wrap
old_btn_wrap = '''                  <div class="d-flex justify-content-end">
                    <button type="button" class="btn btn-success" id="btnUploadCourses" onclick="doPreviewCourses()"><i class="bi bi-lightning-charge me-1"></i>Pre-visualizar</button>
                  </div>'''
html = html.replace(old_btn_wrap, "")

# 3. Modify the preview wrapper. It shouldn't have "Cancelar y Volver", just the confirm button, because it's inline.
old_preview_buttons = '''              <div class="d-flex justify-content-end gap-2 mt-4">
                <button type="button" class="btn btn-outline-secondary" onclick="cancelPreviewCourses()">Cancelar y Volver</button>
                <button type="button" class="btn btn-success" id="btnConfirmCourses" onclick="executeCreateCourses()">
                  <i class="bi bi-check-circle me-1"></i>Confirmar y Crear Cursos
                </button>
              </div>'''
new_preview_buttons = '''              <div class="d-flex justify-content-end mt-4">
                <button type="button" class="btn btn-success" id="btnConfirmCourses" onclick="executeCreateCourses()">
                  <i class="bi bi-check-circle me-1"></i>Confirmar y Crear Cursos
                </button>
              </div>'''
html = html.replace(old_preview_buttons, new_preview_buttons)

# 4. Update JS logic: 
# Remove FormHide
old_js_hide = "document.getElementById('coursesOdFormWrap').style.display = 'none';"
html = html.replace(old_js_hide, "")

# Remove Cancel function body (but keep function just in case)
old_cancel = '''function cancelPreviewCourses() {
    document.getElementById('coursesOdPreviewWrap').style.display = 'none';
    document.getElementById('coursesOdFormWrap').style.display = 'block';
}'''
new_cancel = '''function cancelPreviewCourses() {
    document.getElementById('coursesOdPreviewWrap').style.display = 'none';
}'''
html = html.replace(old_cancel, new_cancel)

# We should make sure `btnLoadCoursesSheets` disabling doesn't ruin everything.

with open('Frontend/templates/canvas/courses.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("courses.html refactored")
