import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"  # Grafana URL
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")
OUTPUT_DIR = "exported_dashboards"     # папка для сохранения JSON
# ==================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Get all folders
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
if folders_resp.status_code != 200:
    print(f"Unexpected folders response: {folders_resp.json()}")
    folders_list = []
else:
    folders_list = folders_resp.json()

# Loop through each folder
for folder in folders_list:
    folder_name = folder['title']
    folder_id = folder['id']
    folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # 2. Get dashboards in this folder using folder ID
    search_url = f"{GRAFANA_URL}/api/search?type=dash-db&folderIds={folder_id}&limit=1000"
    search_resp = requests.get(search_url, headers=HEADERS)

    if search_resp.status_code != 200:
        print(f"Unexpected dashboards response for folder {folder_name}: {search_resp.json()}")
        dashboards = []
    else:
        dashboards = search_resp.json()

    # 3. Export each dashboard
    for dash in dashboards:
        dash_uid = dash['uid']
        dash_title = dash['title']

        dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)
        if dash_resp.status_code != 200:
            print(f"Failed to get dashboard {dash_title}: {dash_resp.json()}")
            continue

        dash_json = dash_resp.json()['dashboard']
        dash_json['id'] = None  # remove ID to allow re-import

        filename = os.path.join(folder_path, f"{dash_title.replace(' ', '_')}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dash_json, f, indent=2, ensure_ascii=False)

        print(f"Saved dashboard: {folder_name}/{dash_title}")

print("\n✅ Export completed!")
