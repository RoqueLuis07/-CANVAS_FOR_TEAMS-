import os
import sys

sys.path.insert(0, os.path.abspath('Backend'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

urls = {
    "Cursos": {
        "url": "https://usilparaguay-my.sharepoint.com/:x:/g/personal/resteche_usil_edu_py/IQARA_HJhg00QKcvL8bD1WvnATEbShmJ6jbq6qzgbWLzqIc?e=BayIS2",
        "sheets_ep": "/excel/courses/sheets",
        "preview_ep": "/excel/courses/preview"
    },
    "Diplomados": {
        "url": "https://usilparaguay-my.sharepoint.com/:x:/g/personal/resteche_usil_edu_py/IQBjeh0nYFG7QbZx21y-3U-8AfhP2B9akxz7fo_LK_sKyGo?e=tXi91Q",
        "sheets_ep": "/excel/diplomados/sheets",
        "preview_ep": "/excel/diplomados/preview"
    },
    "Matriculaciones": {
        "url": "https://usilparaguay-my.sharepoint.com/:x:/g/personal/resteche_usil_edu_py/IQCHMuoLYGs9T4NDeid5n9A7AZvphg9oml_g9dt-GYD5tY0?e=d4RKCr",
        "sheets_ep": "/excel/matriculaciones-onedrive/sheets",
        "preview_ep": "/excel/matriculaciones-onedrive/preview"
    },
    "UsuariosMasivo": {
        "url": "https://usilparaguay-my.sharepoint.com/:x:/g/personal/resteche_usil_edu_py/IQA4gwZnz09sSIwlVtQ5bZlmAblW8XRtsRBXTTPnz6UTXjU?e=AlIYI6",
        "sheets_ep": "/excel/masivo/sheets",
        "preview_ep": "/excel/masivo/preview"
    },
    "Docentes": {
        "url": "https://usilparaguay-my.sharepoint.com/:x:/g/personal/resteche_usil_edu_py/IQAXcMN-cm4oQL3gRm2urNcTAeH-gSDKwUwleXVrjyAFcZY?e=GhWnCj",
        "sheets_ep": "/excel/docentes-onedrive/sheets",
        "preview_ep": "/excel/docentes-onedrive/preview"
    }
}

for name, info in urls.items():
    print(f"\\n{'='*50}\\nTesting {name}\\n{'='*50}")
    url = info["url"]
    
    # 1. Get sheets
    res = client.post(info["sheets_ep"], json={"url": url})
    if res.status_code != 200:
        print(f"FAILED to get sheets: {res.status_code} - {res.text}")
        continue
        
    data = res.json()
    sheets = data.get("sheets", [])
    print(f"Found sheets: {sheets}")
    
    if not sheets:
        print("No sheets found to preview.")
        continue
        
    # 2. Preview the first sheet
    sheet_name = sheets[0]
    print(f"Previewing sheet: {sheet_name}")
    
    res_prev = client.post(info["preview_ep"], json={"url": url, "sheet_name": sheet_name})
    if res_prev.status_code != 200:
        print(f"FAILED to preview sheet: {res_prev.status_code} - {res_prev.text}")
    else:
        prev_data = res_prev.json()
        print("Preview successful! Output keys:")
        print(list(prev_data.keys()))
        if "headers" in prev_data:
            print("Headers detected:", prev_data["headers"])
        if "student_details" in prev_data:
            print(f"Parsed normalized rows (first 2): {prev_data['student_details'][:2]}")
        elif "course_details" in prev_data:
            print(f"Parsed normalized rows (first 2): {prev_data['course_details'][:2]}")
        elif "sample_rows" in prev_data:
            print(f"Parsed sample rows (first 2): {prev_data['sample_rows'][:2]}")

