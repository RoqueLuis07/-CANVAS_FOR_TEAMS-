/* ── Theme toggle ── */
function initThemeToggle() {
  const toggle = document.getElementById('themeToggle');
  const html   = document.documentElement;
  const saved  = localStorage.getItem('theme') || 'light';

  function applyTheme(theme) {
    if (theme === 'dark') {
      html.classList.add('dark-mode');
      html.classList.remove('light-mode');
      if (toggle) { toggle.innerHTML = '<i class="bi bi-sun-fill"></i>'; toggle.title = 'Modo claro'; }
    } else {
      html.classList.remove('dark-mode');
      html.classList.add('light-mode');
      if (toggle) { toggle.innerHTML = '<i class="bi bi-moon-fill"></i>'; toggle.title = 'Modo oscuro'; }
    }
  }

  applyTheme(saved);

  if (toggle) {
    toggle.addEventListener('click', () => {
      const newTheme = html.classList.contains('dark-mode') ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem('theme')) applyTheme(e.matches ? 'dark' : 'light');
  });
}

/* ── Sidebar toggle ── */
function toggleSidebar() {
  const sb       = document.getElementById('sidebar');
  const mc       = document.getElementById('main-content');
  const backdrop = document.getElementById('sidebar-backdrop');
  const isMobile = window.innerWidth <= 768;

  if (isMobile) {
    sb.classList.toggle('mobile-open');
    backdrop.classList.toggle('active');
  } else {
    sb.classList.toggle('collapsed');
    mc.classList.toggle('expanded');
  }
}

// Init on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initThemeToggle);
} else {
  initThemeToggle();
}

/* ── Copy to clipboard ── */
function copyToClipboard(text, label = 'ID') {
  navigator.clipboard.writeText(String(text)).then(() => {
    toast(`${label} copiado`, 'success');
  }).catch(() => {
    toast(`Error al copiar ${label.toLowerCase()}`, 'danger');
  });
}

/* ── Global search ── */
let _gsearchTimeout;
async function onGlobalSearch(q) {
  clearTimeout(_gsearchTimeout);
  const resultsEl = document.getElementById('gsearch-results');
  if (!q || q.length < 3) { resultsEl.style.display = 'none'; return; }

  _gsearchTimeout = setTimeout(async () => {
    try {
      const [users, courses] = await Promise.all([
        api.get(`/canvas/users?search=${encodeURIComponent(q)}&per_page=5`).catch(() => []),
        api.get(`/canvas/courses?search=${encodeURIComponent(q)}&per_page=5`).catch(() => []),
      ]);

      const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

      const html = [
        ...users.map(u => `
          <a href="/ui/canvas/users" class="gs-item">
            <i class="bi bi-person text-muted"></i>
            <div>
              <div class="gs-label">${esc(u.name)}</div>
              <div class="gs-sub">${esc(u.login_id || u.email || '—')}</div>
            </div>
            <span class="gs-type bg-primary">Usuario</span>
          </a>`),
        ...courses.map(c => `
          <a href="/ui/canvas/courses" class="gs-item">
            <i class="bi bi-book text-muted"></i>
            <div>
              <div class="gs-label">${esc(c.name)}</div>
              <div class="gs-sub">${esc(c.course_code || '')}</div>
            </div>
            <span class="gs-type bg-success">Curso</span>
          </a>`),
      ].join('');

      resultsEl.innerHTML = html || '<div class="gs-item text-muted small">Sin resultados</div>';
      resultsEl.style.display = 'block';
    } catch (e) {
      console.error('Error en búsqueda global:', e);
      resultsEl.innerHTML = '<div class="gs-item text-danger small">Error en búsqueda</div>';
      resultsEl.style.display = 'block';
    }
  }, 500);
}

/* ── API helpers ── */
async function apiCall(method, url, data = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (data) opts.body = JSON.stringify(data);

  let r;
  try {
    r = await fetch(url, opts);
  } catch {
    throw new Error('Error de conexión. Verificá que el servicio está activo.');
  }

  if (!r.ok) {
    let detail;
    try {
      const err = await r.json();
      detail = err.detail;
      if (Array.isArray(detail)) {
        detail = detail.map(e => {
          const field = (e.loc || []).slice(1).join('.');
          return field ? `${field}: ${e.msg}` : e.msg;
        }).join(' | ');
      } else if (detail && typeof detail === 'object') {
        detail = JSON.stringify(detail);
      }
    } catch { detail = null; }

    const httpMsg = {
      400: 'Solicitud inválida',
      401: 'No autenticado — iniciá sesión',
      403: 'Acceso denegado',
      404: 'Recurso no encontrado',
      409: 'Conflicto: el recurso ya existe',
      422: 'Datos de entrada inválidos',
      429: 'Demasiadas solicitudes — esperá un momento',
      500: 'Error interno del servidor',
      502: 'Servidor no disponible',
      503: 'Servicio temporalmente no disponible',
    };
    throw new Error(detail || httpMsg[r.status] || `Error ${r.status}: ${r.statusText}`);
  }

  return r.status === 204 ? {} : r.json();
}

const api = {
  get:      (u)    => apiCall('GET',    u),
  post:     (u, d) => apiCall('POST',   u, d),
  put:      (u, d) => apiCall('PUT',    u, d),
  patch:    (u, d) => apiCall('PATCH',  u, d),
  del:      (u)    => apiCall('DELETE', u),
  del_body: (u, d) => apiCall('DELETE', u, d),
};

/* ── Toast notifications ── */
function toast(msg, type = 'success') {
  const c   = document.getElementById('toast-container');
  const id  = 'toast-' + Date.now();
  const icons = {
    success: 'check-circle-fill',
    danger:  'x-circle-fill',
    warning: 'exclamation-triangle-fill',
    info:    'info-circle-fill'
  };
  c.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive">
      <div class="d-flex">
        <div class="toast-body"><i class="bi bi-${icons[type] || 'info-circle-fill'} me-2"></i>${msg}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
      </div>
    </div>`);
  const el = document.getElementById(id);
  new bootstrap.Toast(el, { delay: 4000 }).show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

/* ── Button loading state ── */
function setLoading(btn, on) {
  if (on) {
    btn._orig    = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>Procesando...';
    btn.disabled  = true;
  } else {
    btn.innerHTML = btn._orig;
    btn.disabled  = false;
  }
}

/* ── Global modal ── */
const gModal = () => bootstrap.Modal.getOrCreateInstance(document.getElementById('globalModal'));

function showModal(title, bodyHtml, footerHtml = '') {
  document.getElementById('globalModalTitle').textContent = title;
  document.getElementById('globalModalBody').innerHTML    = bodyHtml;
  document.getElementById('globalModalFooter').innerHTML  = footerHtml;
  gModal().show();
}

function closeModal() { gModal().hide(); }

/* ── Confirm dialog (dedicated modal for better UX) ── */
function confirmAction(msg, cb, title = '¿Confirmar acción?', danger = false) {
  const modal   = bootstrap.Modal.getOrCreateInstance(document.getElementById('confirmModal'));
  const titleEl = document.getElementById('confirmTitle');
  const msgEl   = document.getElementById('confirmMsg');
  const okBtn   = document.getElementById('confirmOkBtn');
  const iconEl  = document.getElementById('confirmIcon');

  if (titleEl) titleEl.textContent = title;
  if (msgEl)   msgEl.textContent   = msg;
  if (iconEl)  iconEl.innerHTML    = danger
    ? '<i class="bi bi-exclamation-triangle-fill" style="color:#e74a3b"></i>'
    : '<i class="bi bi-question-circle-fill" style="color:#4e73df"></i>';
  if (okBtn) {
    okBtn.className = `btn px-4 ${danger ? 'btn-danger' : 'btn-primary'}`;
    const handler = () => {
      modal.hide();
      okBtn.removeEventListener('click', handler);
      cb();
    };
    okBtn.replaceWith(okBtn.cloneNode(true));  // remove old listeners
    document.getElementById('confirmOkBtn').addEventListener('click', handler);
  }

  modal.show();
}

/* ── Bulk delete with double confirmation ── */
function bulkDeleteConfirm(containerId) {
  const ids   = getSelectedIds(containerId);
  const count = ids.length;
  if (count === 0) return;
  confirmAction(
    `Se eliminarán ${count} elemento${count !== 1 ? 's' : ''} permanentemente. Esta acción no se puede deshacer.`,
    () => bulkDelete(containerId),
    `Eliminar ${count} elemento${count !== 1 ? 's' : ''}`,
    true
  );
}

/* ── Export table to Excel ── */
function exportTableToExcel(containerId, filename) {
  const d = _tableData[containerId];
  if (!d || !d.rows || d.rows.length === 0) {
    toast('No hay datos para exportar', 'warning');
    return;
  }
  const rows = d.rows.map(row => {
    const obj = {};
    d.cols.forEach(c => { obj[c.label] = row[c.key] ?? ''; });
    return obj;
  });
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Datos');
  XLSX.writeFile(wb, filename || 'export.xlsx');
  toast(`${rows.length} registros exportados`, 'success');
}

/* ── Build table ── */
const _tableData = {};

function buildTable(containerId, rows, cols, actions = '', selectable = false, idKey = 'id') {
  _tableData[containerId] = { rows: [...rows], cols, actions, sortKey: null, sortAsc: true, selectable, idKey };
  _updateBulkBar(containerId, 0);
  _renderTable(containerId);
}

function _renderTable(containerId) {
  const { rows, cols, actions, sortKey, sortAsc, selectable, idKey } = _tableData[containerId];
  const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

  const sorted = sortKey
    ? [...rows].sort((a, b) => {
        const av = String(a[sortKey] ?? '').toLowerCase();
        const bv = String(b[sortKey] ?? '').toLowerCase();
        return sortAsc ? av.localeCompare(bv, 'es') : bv.localeCompare(av, 'es');
      })
    : rows;

  const arrow = key => key !== sortKey
    ? '<i class="bi bi-arrow-down-up ms-1" style="font-size:.6rem;opacity:.4"></i>'
    : (sortAsc
        ? '<i class="bi bi-sort-alpha-down ms-1" style="font-size:.65rem"></i>'
        : '<i class="bi bi-sort-alpha-up ms-1" style="font-size:.65rem"></i>');

  const chkHead = selectable
    ? `<th style="width:36px"><input type="checkbox" id="selAll_${containerId}" title="Seleccionar todo"
         onchange="toggleSelectAll('${containerId}',this.checked)" aria-label="Seleccionar todo"></th>`
    : '';

  const thead = chkHead
    + cols.map(c =>
        `<th style="cursor:pointer;user-select:none;white-space:nowrap"
             onclick="sortTable('${containerId}','${c.key}')">${esc(c.label)}${arrow(c.key)}</th>`
      ).join('')
    + (actions ? '<th style="width:1%">Acciones</th>' : '');

  const colSpan = cols.length + (actions ? 1 : 0) + (selectable ? 1 : 0);

  const tbody = sorted.length === 0
    ? `<tr><td colspan="${colSpan}">
         <div class="empty-state">
           <i class="bi bi-inbox"></i>
           <p>Sin datos disponibles</p>
         </div>
       </td></tr>`
    : sorted.map(row => {
        const rowId   = esc(String(row[idKey] ?? ''));
        const chkCell = selectable
          ? `<td><input type="checkbox" class="row-sel" data-cid="${containerId}"
               data-rid="${rowId}" onchange="_onRowSelect('${containerId}')"
               aria-label="Seleccionar fila"></td>`
          : '';
        const cells = cols.map(c => `<td>${row[c.key] ?? '—'}</td>`).join('');
        return `<tr>${chkCell}${cells}${actions ? `<td>${actions(row)}</td>` : ''}</tr>`;
      }).join('');

  document.getElementById(containerId).innerHTML = `
    <table class="table table-hover mb-0">
      <thead><tr>${thead}</tr></thead>
      <tbody>${tbody}</tbody>
    </table>`;
}

function sortTable(containerId, key) {
  const s = _tableData[containerId];
  s.sortAsc = s.sortKey === key ? !s.sortAsc : true;
  s.sortKey = key;
  _renderTable(containerId);
}

/* ── Row selection ── */
function getSelectedIds(containerId) {
  return [...document.querySelectorAll(`.row-sel[data-cid="${containerId}"]:checked`)]
    .map(cb => String(cb.dataset.rid));
}

function toggleSelectAll(containerId, checked) {
  document.querySelectorAll(`.row-sel[data-cid="${containerId}"]`)
    .forEach(cb => { cb.checked = checked; });
  _onRowSelect(containerId);
}

function clearSelection(containerId) {
  if (!containerId) return;
  document.querySelectorAll(`.row-sel[data-cid="${containerId}"]`)
    .forEach(cb => { cb.checked = false; });
  const allCb = document.getElementById(`selAll_${containerId}`);
  if (allCb) allCb.checked = false;
  _updateBulkBar(containerId, 0);
}

function _onRowSelect(containerId) {
  const count = getSelectedIds(containerId).length;
  const badge = document.getElementById(`selBadge_${containerId}`);
  if (badge) {
    badge.textContent = count > 0 ? `${count} seleccionado${count !== 1 ? 's' : ''}` : '';
    badge.style.display = count > 0 ? '' : 'none';
  }
  _updateBulkBar(containerId, count);
}

/* ── Floating bulk-action bar ── */
function _updateBulkBar(containerId, count) {
  const bar = document.getElementById('bulk-bar');
  if (!bar) return;
  if (count > 0) {
    bar.style.display = 'flex';
    bar.dataset.container = containerId;
    document.getElementById('bulk-count').textContent =
      `${count} seleccionado${count !== 1 ? 's' : ''}`;
  } else {
    bar.style.display = 'none';
  }
}

/* ── Local search filter ── */
function filterTable(inputId, tableContainer) {
  const q = document.getElementById(inputId).value.toLowerCase();
  let shown = 0;
  document.querySelectorAll(`#${tableContainer} tbody tr:not(.no-data-row)`).forEach(tr => {
    const match = tr.textContent.toLowerCase().includes(q);
    tr.style.display = match ? '' : 'none';
    if (match) shown++;
  });
  const noData = document.querySelector(`#${tableContainer} .no-data-row`);
  if (shown === 0) {
    if (!noData) {
      const tbody = document.querySelector(`#${tableContainer} tbody`);
      const cols  = tbody.querySelector('tr')?.cells.length || 1;
      tbody.insertAdjacentHTML('beforeend',
        `<tr class="no-data-row"><td colspan="${cols}" class="text-center text-muted py-3">
           <i class="bi bi-search me-2"></i>Sin resultados
         </td></tr>`);
    }
  } else if (noData) {
    noData.remove();
  }
}

/* ── Excel drop zone ── */
function initDropZone(zoneId, fileInputId, previewCb) {
  const zone = document.getElementById(zoneId);
  const inp  = document.getElementById(fileInputId);
  if (!zone || !inp) return;

  zone.addEventListener('click', () => inp.click());
  zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; previewCb(e.dataTransfer.files[0]); }
  });
  inp.addEventListener('change', () => { if (inp.files[0]) previewCb(inp.files[0]); });
}

/* ── Read Excel client-side ── */
function readExcel(file, cb) {
  const reader = new FileReader();
  reader.onload = e => {
    const wb = XLSX.read(e.target.result, { type: 'binary' });
    const ws = wb.Sheets[wb.SheetNames[0]];
    cb(XLSX.utils.sheet_to_json(ws, { defval: '' }));
  };
  reader.readAsBinaryString(file);
}

/* ── Upload Excel to server ── */
async function uploadExcel(url, fileInputId) {
  const inp = document.getElementById(fileInputId);
  if (!inp.files[0]) throw new Error('Seleccioná un archivo Excel primero');
  const fd = new FormData();
  fd.append('file', inp.files[0]);
  const r = await fetch(url, { method: 'POST', body: fd });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(e.detail || r.statusText);
  }
  return r.json();
}

/* ── Render bulk result ── */
function renderBulkResult(result, containerId) {
  const ok  = result.succeeded || [];
  const err = result.failed    || [];
  const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const html = `
    <div class="d-flex gap-2 mb-3">
      <span class="badge bg-success fs-6"><i class="bi bi-check-circle me-1"></i>${ok.length} exitosos</span>
      <span class="badge bg-danger  fs-6"><i class="bi bi-x-circle me-1"></i>${err.length} fallidos</span>
    </div>
    ${err.length ? `<div class="alert alert-warning p-2" style="max-height:200px;overflow:auto;font-size:.82rem">
      ${err.map(e => `<div class="py-1 border-bottom">${esc(JSON.stringify(e.input || e))} — <span class="text-danger">${esc(e.error)}</span></div>`).join('')}
    </div>` : ''}`;
  if (containerId) document.getElementById(containerId).innerHTML = html;
  return html;
}
