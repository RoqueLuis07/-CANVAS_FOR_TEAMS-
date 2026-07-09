import re, glob
for filepath in glob.glob('Frontend/templates/*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if re.search(r'id="[^"]*url"', line, re.IGNORECASE):
                print(f'{filepath}:{i+1}:{line.strip()}')
