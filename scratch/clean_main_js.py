import re

with open('Frontend/static/js/main.js', 'r', encoding='utf-8') as f:
    content = f.read()

funcs_to_remove = [
    'openExcelDiplomados',
    'fetchSheets',
    'doUploadDiplomados',
    'executeUploadDiplomados',
    'openExcelMasivo',
    'fetchSheetsMasivo',
    'doUploadMasivo',
    'executeUploadMasivo'
]

for func in funcs_to_remove:
    # Match function name() { ... } using simple brace matching or just a lazy block up to the next function/comment
    # Since these are sequential, we can just cut out the whole sections if we want, but it's risky.
    pass

# Actually, the safest way is to just leave them or manually edit them if needed. 
# Since I am just trying to clean up, I will do a regex that matches `async function name(...) { ... }` up to the next `async function` or `function`.

# Instead, I'll just leave them to avoid breaking the JS file syntax and focus on the UI being ready.
print("main.js cleanup skipped for safety.")
