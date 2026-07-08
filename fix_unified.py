
import re
with open('Frontend/templates/unified_enrollments.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'let modalMat;\s*if \(!modalMat\).*?modalMat\.show\(\);\s*', re.DOTALL)
content = pattern.sub('', content)

with open('Frontend/templates/unified_enrollments.html', 'w', encoding='utf-8') as f:
    f.write(content)

