import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"  # Grafana URL
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")  # Token from environment variable
OUTPUT_DIR = "exported_dashboards"
# ==================

if not API_TOKEN:
    raise ValueError("Environment variable GRAFANA_API_TOKEN is not set!")

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
    print("Error decoding folders response:", folders_resp.text)
    folders_list = []

# Add General (default) folder
folders_list.insert(0, {"uid": "", "title": "General"})

# 2. Export dashboards per folder
for folder in folders_list:
    folder_name = folder['title']
    folder_uid = folder['uid']  # can be empty string for General
    folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # Get dashboards in the folder
    search_url = f"{GRAFANA_URL}/api/search?type=dash-db"
    if folder_uid:
        search_url += f"&folderIds={folder_uid}"

    search_resp = requests.get(search_url, headers=HEADERS)
    try:
        dashboards = search_resp.json()
    except json.JSONDecodeError:
        print(f"Error decoding dashboards for folder {folder_name}:", search_resp.text)
        dashboards = []

    if not dashboards:
        print(f"No dashboards found in folder {folder_name}")
        continue

    for dash in dashboards:
        dash_uid = dash['uid']
        dash_title = dash['title']

        dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)
        try:
            dash_json = dash_resp.json()['dashboard']
        except (json.JSONDecodeError, KeyError):
            print(f"Error fetching dashboard {dash_title} in folder {folder_name}")
            continue

        dash_json['id'] = None  # remove id to allow import

        filename = os.path.join(folder_path, f"{dash_title.replace(' ', '_')}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dash_json, f, indent=2, ensure_ascii=False)

        print(f"Saved dashboard: {folder_name}/{dash_title}")

print("\n✅ Export completed!")
