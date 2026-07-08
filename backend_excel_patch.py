
import re
with open('Backend/app/routers/excel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update PreviewResponse
content = re.sub(
    r'class PreviewResponse\(BaseModel\):\n    sheet_name: str\n    students_to_process: int\n    students_already_processed: int\n    student_details: list\[dict\]',
    'class PreviewResponse(BaseModel):\n    sheet_name: str\n    students_to_process: int\n    students_already_processed: int\n    student_details: list[dict]\n    headers: list[str] = []\n    sample_rows: list[dict] = []',
    content
)

# 2. Update CoursesPreviewResponse
content = re.sub(
    r'class CoursesPreviewResponse\(BaseModel\):\n    sheet_name: str\n    courses_to_create: int\n    courses_already_created: int\n    course_details: list\[dict\]',
    'class CoursesPreviewResponse(BaseModel):\n    sheet_name: str\n    courses_to_create: int\n    courses_already_created: int\n    course_details: list[dict]\n    headers: list[str] = []\n    sample_rows: list[dict] = []',
    content
)

# 3. Update DocentesPreviewResponse
content = re.sub(
    r'class DocentesPreviewResponse\(BaseModel\):\n    total_rows: int\n    valid_rows: int\n    sample: list\[dict\]',
    'class DocentesPreviewResponse(BaseModel):\n    total_rows: int\n    valid_rows: int\n    sample: list[dict]\n    headers: list[str] = []',
    content
)

with open('Backend/app/routers/excel.py', 'w', encoding='utf-8') as f:
    f.write(content)

