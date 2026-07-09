import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

base_url = "https://canvasforteams-production-689d.up.railway.app"

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
        "sheets_ep": None, # Masivo doesnt have a sheets endpoint
        "preview_ep": "/excel/masivo/preview"
    },
    "Docentes": {
        "url": "https://usilparaguay-my.sharepoint.com/:x:/g/personal/resteche_usil_edu_py/IQAXcMN-cm4oQL3gRm2urNcTAeH-gSDKwUwleXVrjyAFcZY?e=GhWnCj",
        "sheets_ep": "/excel/docentes-onedrive/sheets",
        "preview_ep": "/excel/docentes-onedrive/preview"
    }
}

for name, info in urls.items():
    print(f"\\n================================\\nTesting {name}\\n================================")
    url = info["url"]
    
    sheet_to_preview = None
    
    if info["sheets_ep"]:
        res = requests.post(f"{base_url}{info['sheets_ep']}", json={"url": url})
        if res.status_code != 200:
            print(f"FAILED to get sheets: {res.status_code} - {res.text}")
            continue
        data = res.json()
        sheets = data if isinstance(data, list) else data.get("sheets", [])
        print(f"Sheets: {sheets}")
        if not sheets:
            continue
        sheet_to_preview = sheets[0]
        print(f"Will preview sheet: {sheet_to_preview}")
    else:
        print("No sheets endpoint, previewing default sheet.")
        
    payload = {"url": url}
    if sheet_to_preview:
        payload["sheet_name"] = sheet_to_preview
        
    res_prev = requests.post(f"{base_url}{info['preview_ep']}", json=payload)
    if res_prev.status_code != 200:
        print(f"FAILED preview: {res_prev.status_code} - {res_prev.text}")
    else:
        prev_data = res_prev.json()
        print("SUCCESS preview!")
        for k in ["headers", "student_details", "course_details", "sample_rows", "sample"]:
            if k in prev_data:
                print(f"  {k}: {prev_data[k][:2] if isinstance(prev_data[k], list) else prev_data[k]}")
