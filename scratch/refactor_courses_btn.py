import re

with open('Frontend/templates/canvas/courses.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove Pre-visualizar button block
html = re.sub(
    r'<div class="d-flex justify-content-end">\s*<button type="button" class="btn btn-success" id="btnUploadCourses" onclick="doPreviewCourses\(\)">.*?Pre-visualizar</button>\s*</div>',
    '',
    html,
    flags=re.DOTALL
)

with open('Frontend/templates/canvas/courses.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("courses.html pre-visualizar button removed")
