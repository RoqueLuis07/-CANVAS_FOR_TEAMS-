import re

with open('Frontend/templates/unified_enrollments.html', 'r', encoding='utf-8') as f:
    content = f.read()

js_code = """
let mi_materiasList = []; // from backend
let mi_selectedMaterias = [];

async function mi_onProgramChange() {
    const prog = document.getElementById('mi_programa').value;
    const searchInput = document.getElementById('mi_search');
    const list = document.getElementById('mi_autocomplete_list');
    
    if (!prog) {
        searchInput.disabled = true;
        list.style.display = 'none';
        return;
    }
    
    searchInput.disabled = false;
    searchInput.value = '';
    list.style.display = 'none';
    
    try {
        const res = await api.get('/api/matriculacion/materias?program=' + prog);
        mi_materiasList = res || [];
    } catch (e) {
        toast('Error al cargar materias del programa: ' + e.message, 'danger');
        mi_materiasList = [];
    }
}

function mi_onSearchInput() {
    const q = document.getElementById('mi_search').value.toLowerCase();
    const list = document.getElementById('mi_autocomplete_list');
    
    if (q.length < 2) {
        list.style.display = 'none';
        return;
    }
    
    const matches = mi_materiasList.filter(m => 
        (m.name.toLowerCase().includes(q) || m.id.toLowerCase().includes(q)) && 
        !mi_selectedMaterias.find(sel => sel.id === m.id)
    );
    
    if (matches.length === 0) {
        list.style.display = 'none';
        return;
    }
    
    list.innerHTML = matches.map(m => `
        <li class="list-group-item list-group-item-action cursor-pointer" onclick="mi_addMateria('${m.id}')">
            <strong>${m.id}</strong> - ${m.name}
        </li>
    `).join('');
    list.style.display = 'block';
}

function mi_addMateria(id) {
    const m = mi_materiasList.find(x => x.id === id);
    if (!m) return;
    
    if (!mi_selectedMaterias.find(sel => sel.id === id)) {
        mi_selectedMaterias.push(m);
        mi_renderSelected();
    }
    
    document.getElementById('mi_search').value = '';
    document.getElementById('mi_autocomplete_list').style.display = 'none';
}

function mi_removeMateria(id) {
    mi_selectedMaterias = mi_selectedMaterias.filter(x => x.id !== id);
    mi_renderSelected();
}

function mi_renderSelected() {
    const container = document.getElementById('mi_tags_container');
    const msg = document.getElementById('mi_empty_msg');
    
    if (mi_selectedMaterias.length === 0) {
        container.innerHTML = '';
        msg.style.display = 'block';
        return;
    }
    
    msg.style.display = 'none';
    container.innerHTML = mi_selectedMaterias.map(m => `
        <span class="badge bg-primary fs-6 d-flex align-items-center gap-2 p-2">
            ${m.id} - ${m.name}
            <i class="bi bi-x-circle-fill cursor-pointer text-white-50" onclick="mi_removeMateria('${m.id}')" title="Quitar"></i>
        </span>
    `).join('');
}

function mi_resetForm() {
    document.getElementById('mi_correo').value = '';
    document.getElementById('mi_sys').value = '';
    document.getElementById('mi_programa').value = '';
    document.getElementById('mi_search').value = '';
    document.getElementById('mi_plataforma').value = 'both';
    document.getElementById('mi_resultWrap').style.display = 'none';
    mi_selectedMaterias = [];
    mi_renderSelected();
    mi_onProgramChange();
}

async function mi_doEnroll() {
    const email = document.getElementById('mi_correo').value.trim();
    const sys = document.getElementById('mi_sys').value.trim();
    const prog = document.getElementById('mi_programa').value;
    const plat = document.getElementById('mi_plataforma').value;
    const btn = document.getElementById('btnMatriculacionInd');
    const resultWrap = document.getElementById('mi_resultWrap');
    
    if (!email || !sys || !prog) {
        toast('Complete los campos obligatorios (Correo, SYS, Programa).', 'warning');
        return;
    }
    if (mi_selectedMaterias.length === 0) {
        toast('Debe seleccionar al menos una materia.', 'warning');
        return;
    }
    
    setLoading(btn, true);
    resultWrap.style.display = 'none';
    
    try {
        const payload = {
            email: email,
            sys_id: sys,
            program: prog,
            materias: mi_selectedMaterias,
            platforms: plat
        };
        
        const res = await api.post('/api/matriculacion/individual', payload);
        
        let html = `<strong>Matriculación Completada</strong><ul class="mb-0 mt-2">`;
        res.results.forEach(r => {
            html += `<li><strong>${r.materia_name}</strong> - Canvas: ${r.canvas_status} | Teams: ${r.teams_status}</li>`;
        });
        html += `</ul>`;
        
        resultWrap.innerHTML = html;
        resultWrap.className = 'alert alert-success mb-4';
        resultWrap.style.display = 'block';
        toast('Proceso completado', 'success');
        
        mi_loadHistory();
    } catch (e) {
        resultWrap.innerHTML = `<strong>Error:</strong> ${e.message}`;
        resultWrap.className = 'alert alert-danger mb-4';
        resultWrap.style.display = 'block';
        toast('Error en matriculación', 'danger');
    } finally {
        setLoading(btn, false);
    }
}

async function mi_loadHistory() {
    try {
        const history = await api.get('/api/matriculacion/history');
        const tbody = document.getElementById('mi_history_body');
        if (!history || history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No hay registros recientes</td></tr>';
            return;
        }
        
        tbody.innerHTML = history.slice(0, 10).map(h => {
            const dateStr = new Date(h.timestamp).toLocaleString();
            let materiasHtml = h.results.map(r => `<div><span class="badge bg-secondary me-1">${r.materia_id}</span>${r.materia_name}</div>`).join('');
            let canvasHtml = h.results.map(r => `<div>${r.canvas_status === 'OK' ? '<i class="bi bi-check-circle-fill text-success"></i>' : '<i class="bi bi-x-circle-fill text-danger" title="'+r.canvas_status+'"></i>'}</div>`).join('');
            let teamsHtml = h.results.map(r => `<div>${r.teams_status === 'OK' ? '<i class="bi bi-check-circle-fill text-success"></i>' : '<i class="bi bi-x-circle-fill text-danger" title="'+r.teams_status+'"></i>'}</div>`).join('');
            
            return `<tr>
                <td class="small text-muted">${dateStr}</td>
                <td><strong>${h.email}</strong><br><small class="text-muted">SYS: ${h.sys_id}</small></td>
                <td><span class="badge bg-info text-dark">${h.program}</span></td>
                <td class="small">${materiasHtml}</td>
                <td class="text-center">${canvasHtml}</td>
                <td class="text-center">${teamsHtml}</td>
            </tr>`;
        }).join('');
    } catch(e) {
        console.error('Error loading history:', e);
    }
}

// Global click to close autocomplete
document.addEventListener('click', function(e) {
    if(e.target.id !== 'mi_search') {
        const list = document.getElementById('mi_autocomplete_list');
        if(list) list.style.display = 'none';
    }
});

// Load history on mount
document.addEventListener('DOMContentLoaded', () => {
    mi_loadHistory();
});
"""

# Insert JS code into the `<script>` block
content = content.replace('let pendingRollbackIds = [];', js_code + '\nlet pendingRollbackIds = [];')

# Ensure we have cursor-pointer style
if '.cursor-pointer {' not in content:
    style_idx = content.find('<style>')
    if style_idx != -1:
        content = content.replace('<style>', '<style>\n.cursor-pointer { cursor: pointer; }')
    else:
        content = content.replace('{% block content %}', '<style>\n.cursor-pointer { cursor: pointer; }\n</style>\n{% block content %}')

with open('Frontend/templates/unified_enrollments.html', 'w', encoding='utf-8') as f:
    f.write(content)
