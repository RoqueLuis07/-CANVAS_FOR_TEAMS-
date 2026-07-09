import re

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Revert previewRes.sample_rows back to previewRes.sample
text = text.replace('previewRes.sample_rows.map', 'previewRes.sample.map')

# 2. Revert res.sample_rows back to res.sample (temporarily)
text = text.replace('res.sample_rows.map', 'res.sample.map')

# 3. For Diplomados specifically, change to res.student_details.map
diplomados_regex = r"(const res = await api\.post\('/excel/diplomados/preview'.*?tbody\.innerHTML = )res\.sample\.map"
text = re.sub(diplomados_regex, r'\1res.student_details.map', text, flags=re.DOTALL)

# 4. For Masivo specifically, change to res.student_details.map
masivo_regex = r"(const res = await api\.post\('/excel/masivo/preview'.*?tbody\.innerHTML = )res\.sample\.map"
text = re.sub(masivo_regex, r'\1res.student_details.map', text, flags=re.DOTALL)

# 5. For Docentes, change to res.sample_rows.map
docentes_regex = r"(const res = await api\.post\('/excel/docentes-onedrive/preview'.*?tbody\.innerHTML = )res\.sample\.map"
text = re.sub(docentes_regex, r'\1res.sample_rows.map', text, flags=re.DOTALL)

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated ingreso.html")
