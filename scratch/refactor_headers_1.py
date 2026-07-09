import sys
import re

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Inject the helper function right after _get
helper_func = '''def _get(row: dict, *keys) -> Any:
    """Try multiple key variants (Spanish + English) and return the first non-empty value."""
    for k in keys:
        v = row.get(k) or row.get(_norm(k))
        if v is not None and str(v).strip():
            return str(v).strip()
    return None

def _find_header_row_and_headers(ws, max_scan_rows=15):
    """
    Escanea las primeras `max_scan_rows` buscando la fila de encabezados.
    Retorna (header_row_idx, dict_de_headers_normalizados, array_de_headers) o (None, {}, []).
    """
    for row_idx in range(1, min(max_scan_rows, ws.max_row + 1)):
        row_vals = [str(ws.cell(row=row_idx, column=c).value or "").strip() for c in range(1, min(50, ws.max_column + 1))]
        valid_cols = [v for v in row_vals if v]
        if len(valid_cols) >= 2:
            row_str = " ".join(valid_cols).lower()
            if any(keyword in row_str for keyword in ["nombre", "curso", "usuario", "correo", "cedula", "ci", "id canvas", "id teams"]):
                headers_dict = {}
                for col_idx, val in enumerate(row_vals, 1):
                    if val:
                        headers_dict[_norm(val)] = col_idx
                return row_idx, headers_dict, row_vals
                
    return None, {}, []
'''

if 'def _find_header_row_and_headers' not in content:
    content = re.sub(r'def _get\(.*?\)\s*->\s*Any:.*?return None\n', helper_func, content, flags=re.DOTALL)
    print("Injected _find_header_row_and_headers")

# We will let the python script handle the replacements, I'll write the regexes next.
with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)
