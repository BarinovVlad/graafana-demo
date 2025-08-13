import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"   # Grafana URL
API_TOKEN = "YOUR_API_TOKEN"            # Insert your API token here
OUTPUT_DIR = "exported_dashboards"      # Directory to save dashboards
# ==================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Get all folders
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
folders_json = folders_resp.json()

# Ensure we have a list of folders
if isinstance(folders_json, dict):
    # Some Grafana versions return dict with key 'folders'
    folders_list = folders_json.get('folders', [])
elif isinstance(folders_json, list):
    folders_list = folders_json
else:
    folders_list = []

# Add root folder (General)
folders_list.insert(0, {"uid": "", "title": "General"})

# 2. Loop through each folder
for folder in folders_list:
    folder_name = folder.get('title', 'Unknown')
    folder_uid = folder.get('uid', '') if folder.get('uid') else "general"
    folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # Get dashboards in folder
    search_resp = requests.get(
        f"{GRAFANA_URL}/api/search?folderIds={folder_uid}&type=dash-db",
        headers=HEADERS
    )
    dashboards = search_resp.json()

    for dash in dashboards:
        if not isinstance(dash, dict):
            continue

        dash_uid = dash.get('uid')
        dash_title = dash.get('title')

        if not dash_uid or not dash_title:
            continue

        dash_resp = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}",
            headers=HEADERS
        )
        dash_json = dash_resp.json()['dashboard']
        dash_json['id'] = None

        filename = os.path.join(folder_path, f"{dash_title.replace(' ', '_')}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dash_json, f, indent=2, ensure_ascii=False)

        print(f"Saved dashboard: {folder_name}/{dash_title}")

print("\n✅ Export completed!")
