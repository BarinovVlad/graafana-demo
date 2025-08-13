import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"  # Grafana URL
API_TOKEN = "sa-1-github-ci-89f10ad7-2db9-4b29-bd3f-d6808007cfb7"           # Вставь сюда свой API Token
OUTPUT_DIR = "exported_dashboards"     # Папка для экспорта
# ==================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Get all folders
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
try:
    folders_list = folders_resp.json()
except json.JSONDecodeError:
    print("Error decoding folders response")
    folders_list = []

# Ensure response is a list
if not isinstance(folders_list, list):
    print("Unexpected folders response:", folders_list)
    folders_list = []

# Add root "General" folder
folders_list = [{"id": 0, "uid": "", "title": "General"}] + folders_list

# 2. For each folder, export dashboards
for folder in folders_list:
    folder_title = folder['title']
    folder_uid = folder['uid'] if folder['uid'] else ""
    folder_path = os.path.join(OUTPUT_DIR, folder_title.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # Get dashboards in the folder
    search_resp = requests.get(
        f"{GRAFANA_URL}/api/search?folderIds={folder_uid}&query=&type=dash-db",
        headers=HEADERS
    )
    try:
        dashboards_list = search_resp.json()
    except json.JSONDecodeError:
        print(f"Error decoding dashboards for folder {folder_title}")
        dashboards_list = []

    if not isinstance(dashboards_list, list):
        print(f"Unexpected dashboards response for folder {folder_title}:", dashboards_list)
        dashboards_list = []

    for dash in dashboards_list:
        dash_uid = dash.get('uid')
        dash_title = dash.get('title', 'unknown_dashboard')

        if not dash_uid:
            print(f"Skipping dashboard without UID in folder {folder_title}")
            continue

        dash_resp = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}",
            headers=HEADERS
        )
        try:
            dash_json = dash_resp.json()['dashboard']
        except (json.JSONDecodeError, KeyError):
            print(f"Error fetching dashboard {dash_title}")
            continue

        # Remove id to allow re-import
        dash_json['id'] = None

        filename = os.path.join(folder_path, f"{dash_title.replace(' ', '_')}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dash_json, f, indent=2, ensure_ascii=False)

        print(f"Saved dashboard: {folder_title}/{dash_title}")

print("\n✅ Export completed!")
