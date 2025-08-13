import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")
OUTPUT_DIR = "exported_dashboards"
# ==================

if not API_TOKEN:
    raise ValueError("Environment variable GRAFANA_API_TOKEN is not set!")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Get all folders from Grafana
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
folders_list = folders_resp.json() if folders_resp.status_code == 200 else []

if not folders_list:
    print("No folders found in Grafana")
else:
    for folder in folders_list:
        folder_id = folder["id"]
        folder_name = folder["title"]
        folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
        os.makedirs(folder_path, exist_ok=True)

        # 2. Get dashboards in this folder
        search_resp = requests.get(f"{GRAFANA_URL}/api/search?type=dash-db&folderIds={folder_id}", headers=HEADERS)
        dashboards = search_resp.json() if search_resp.status_code == 200 else []

        if not dashboards:
            print(f"No dashboards found in folder {folder_name}")
            continue

        for dash in dashboards:
            dash_uid = dash["uid"]
            dash_title = dash["title"]

            dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)
            if dash_resp.status_code != 200:
                print(f"Error fetching dashboard {dash_title}")
                continue

            dash_json = dash_resp.json()["dashboard"]
            dash_json["id"] = None  # remove id for import

            filename = os.path.join(folder_path, f"{dash_title.replace(' ', '_')}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(dash_json, f, indent=2, ensure_ascii=False)

            print(f"Saved dashboard: {folder_name}/{dash_title}")

print("\n✅ Export completed!")
