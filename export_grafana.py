import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"           # Grafana URL
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")      # API token from environment variable
OUTPUT_DIR = "exported_dashboards"              # Directory to save JSON files
# ==================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Get all folders
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
folders_list = []

if folders_resp.status_code == 200:
    folders_list = folders_resp.json()
else:
    print(f"Unexpected folders response: {folders_resp.json()}")

# 2. Loop through each folder
for folder in folders_list:
    folder_name = folder['title']
    folder_uid = folder['uid']
    folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # Get dashboards in the folder
    search_url = f"{GRAFANA_URL}/api/search?type=dash-db&folderIds={folder_uid}&limit=1000"
    search_resp = requests.get(search_url, headers=HEADERS)

    dashboards = []
    if search_resp.status_code == 200:
        dashboards = search_resp.json()
    else:
        print(f"Unexpected dashboards response for folder {folder_name}: {search_resp.json()}")

    # Export each dashboard using UID
    for dash in dashboards:
        dash_uid = dash.get('uid')
        if not dash_uid:
            continue

        dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)
        if dash_resp.status_code != 200:
            print(f"Failed to fetch dashboard UID {dash_uid}: {dash_resp.json()}")
            continue

        dash_json = dash_resp.json().get('dashboard', {})
        dash_json['id'] = None  # Remove ID for import

        # Save file as uid.json
        filename = os.path.join(folder_path, f"{dash_uid}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dash_json, f, indent=2, ensure_ascii=False)

        print(f"Saved dashboard UID {dash_uid} in folder {folder_name}")

print("\n✅ Export completed!")
