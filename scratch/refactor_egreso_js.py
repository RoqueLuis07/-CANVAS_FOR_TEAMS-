import os

with open('Frontend/templates/unified_offboarding.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the preview body logic with the Matriculaciones-style dictionary logic
old_js = '''            const tbody = document.getElementById('egresoPreviewBody');
            tbody.innerHTML = '';
            data.sample_rows.forEach(row => {
                tbody.innerHTML += '<tr>' + row.map(cell => `<td>${cell || ''}</td>`).join('') + '</tr>';
            });'''

new_js = '''            const tbody = document.getElementById('egresoPreviewBody');
            let bodyHTML = '';
            data.sample_rows.forEach(r => {
                let rowHtml = '';
                data.headers.forEach(h => {
                    let cellVal = r[h] || '';
                    if (h.toLowerCase().includes('estado') || h.toLowerCase().includes('enviado')) {
                        if (cellVal.toLowerCase() === 'ok' || cellVal.toLowerCase().includes('eliminado') || cellVal.toLowerCase().includes('baja')) {
                            cellVal = `<span class="badge bg-warning text-dark">${cellVal}</span>`;
                        } else if (cellVal.toLowerCase().includes('error')) {
                            cellVal = `<span class="badge bg-danger">${cellVal}</span><span class="badge bg-success ms-1">Reintento</span>`;
                        } else {
                            cellVal = `<span class="badge bg-success">A procesar</span>`;
                        }
                    }
                    rowHtml += `<td>${cellVal}</td>`;
                });
                bodyHTML += `<tr>${rowHtml}</tr>`;
            });
            tbody.innerHTML = bodyHTML;'''

html = html.replace(old_js, new_js)

with open('Frontend/templates/unified_offboarding.html', 'w', encoding='utf-8') as f:
    f.write(html)
