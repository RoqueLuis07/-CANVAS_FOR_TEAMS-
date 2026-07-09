import sys
import re

with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for preview functions:
# headers = []
# sample_rows = []
# header_row_idx = None
# for row_idx in range...
#   ...
#   break
# if not header_row_idx:
preview_pattern = re.compile(
    r'(\s+)headers\s*=\s*\[\]\s+sample_rows\s*=\s*\[\]\s+header_row_idx\s*=\s*None\s+for row_idx in range\(.*?\).*?break\s+if not header_row_idx:',
    re.DOTALL
)

preview_repl = r'''\1sample_rows = []
\1header_row_idx, headers_dict, headers_raw = _find_header_row_and_headers(ws)
\1if not header_row_idx:'''

new_content = preview_pattern.sub(preview_repl, content)

# Also need to replace headers = row_vals usage in preview functions:
# Usually they do:
# for i, h in enumerate(headers):
# We need to ensure `headers` exists and is a list of strings for the frontend
preview_fix_headers = re.compile(
    r'(\s+)(col_\w+\s*=\s*-1\n(\s+col_\w+\s*=\s*-1\n)*\s+for i, h in enumerate\(headers\):)',
    re.DOTALL
)

def fix_headers_repl(match):
    indent = match.group(1)
    original = match.group(2)
    return indent + "headers = [h for h in headers_raw if h]\n" + indent + original.replace('enumerate(headers)', 'enumerate(headers_raw)')

new_content = preview_fix_headers.sub(fix_headers_repl, new_content)

# Fix loop over headers_raw where `h` might be empty
# Actually, the original code did for i, h in enumerate(headers): ...
# Let's ensure the enumerate handles empty strings. The logic does `if "nombre" in h.lower():`
# It's fine since `h` is a string (even if empty).


# Pattern for import functions:
# header_row_idx = None
# headers = {}
# for row_idx in range...
#   ...
#   break
# if not header_row_idx:
import_pattern = re.compile(
    r'(\s+)header_row_idx\s*=\s*None\s+(?:title_val\s*=\s*.*?\n\s+)?headers\s*=\s*\{\}\s+for row_idx in range\(.*?\).*?break\s+if not header_row_idx:',
    re.DOTALL
)

import_repl = r'''\1header_row_idx, headers, _ = _find_header_row_and_headers(ws)
\1if not header_row_idx:'''

new_content = import_pattern.sub(import_repl, new_content)

# For import_courses_onedrive, there might be a difference if it used title_val. Let's see if title_val is used elsewhere.
# In import_diplomados, title_val = next(...) was there. It's safe to just let `headers` be the returned dict.

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("Changes applied via refactor_headers_3.py")
