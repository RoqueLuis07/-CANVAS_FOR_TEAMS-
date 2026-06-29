import re

with open('Backend/app/core/database.py', 'r', encoding='utf-8') as f:
    code = f.read()

header = '''
_conn = None
_db_lock = asyncio.Lock()

def _get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_FILE), check_same_thread=False, timeout=30.0)
    return _conn

async def close_db():
    global _conn
    if _conn:
        _conn.close()
        _conn = None
'''

code = code.replace('DB_FILE = Path(__file__).parent.parent.parent / "app.db"', 'DB_FILE = Path(__file__).parent.parent.parent / "app.db"\n' + header)

code = code.replace('conn = sqlite3.connect(str(DB_FILE))', 'conn = _get_conn()')
code = code.replace('conn.close()', '# conn.close()')

def replacer(m):
    indent = m.group(1)
    stmt = m.group(2)
    return f"{indent}async with _db_lock:\n{indent}    {stmt}"

code = re.sub(r'^( +)(.*await asyncio\.to_thread\(.*?\).*?)$', replacer, code, flags=re.MULTILINE)

with open('Backend/app/core/database.py', 'w', encoding='utf-8') as f:
    f.write(code)
