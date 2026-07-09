import sys

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Docentes
target_doc_select = '<select id="doc_sheet" class="form-select" required>'
repl_doc_select = '<select id="doc_sheet" class="form-select" onchange="previewDocentes()" required>'
if target_doc_select in content:
    content = content.replace(target_doc_select, repl_doc_select)

target_doc_btn = '<button type="button" class="btn btn-outline-secondary" onclick="previewDocentes()" id="btnPreviewDocentes">'
repl_doc_btn = '<button type="button" class="btn btn-outline-secondary d-none" onclick="previewDocentes()" id="btnPreviewDocentes">'
if target_doc_btn in content:
    content = content.replace(target_doc_btn, repl_doc_btn)

# Diplomados
target_dip_select = '<select id="diplomadoSheet" class="form-select" required>'
repl_dip_select = '<select id="diplomadoSheet" class="form-select" onchange="previewDiplomados()" required>'
if target_dip_select in content:
    content = content.replace(target_dip_select, repl_dip_select)
    
target_dip_btn = '<button type="button" class="btn btn-outline-secondary" onclick="previewDiplomados()" id="btnPreviewDiplomados">'
repl_dip_btn = '<button type="button" class="btn btn-outline-secondary d-none" onclick="previewDiplomados()" id="btnPreviewDiplomados">'
if target_dip_btn in content:
    content = content.replace(target_dip_btn, repl_dip_btn)
    
# Masivo (Usuarios)
target_mas_select = '<select id="masivoSheet" class="form-select" required>'
repl_mas_select = '<select id="masivoSheet" class="form-select" onchange="previewMasivo()" required>'
if target_mas_select in content:
    content = content.replace(target_mas_select, repl_mas_select)
    
target_mas_btn = '<button type="button" class="btn btn-outline-secondary" onclick="previewMasivo()" id="btnPreviewMasivo">'
repl_mas_btn = '<button type="button" class="btn btn-outline-secondary d-none" onclick="previewMasivo()" id="btnPreviewMasivo">'
if target_mas_btn in content:
    content = content.replace(target_mas_btn, repl_mas_btn)

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(content)
    
print("Updated ingreso.html for auto preview")
