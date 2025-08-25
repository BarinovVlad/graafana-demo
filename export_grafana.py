import os
import json
import requests
import re

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")

if not API_TOKEN:
    raise ValueError("❌ Environment variable GRAFANA_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

EXPORT_DIR = "exported_dashboards"
os.makedirs(EXPORT_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# === GET FOLDERS ===
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
folders_map = {}  # folderId -> folderTitle

if folders_resp.status_code == 200:
    for folder in folders_resp.json():
        folders_map[folder["id"]] = folder["title"]

# === GET ALL DASHBOARDS ===
search_resp = requests.get(f"{GRAFANA_URL}/api/search?type=dash-db", headers=HEADERS)
if search_resp.status_code != 200:
    raise RuntimeError("❌ Failed to fetch dashboards:", search_resp.text)

dashboards = search_resp.json()

for dash in dashboards:
    dash_uid = dash["uid"]
    dash_title = sanitize_filename(dash["title"])
    folder_id = dash.get("folderId", 0)

    # ❌ Пропускаем General
    if folder_id == 0:
        continue

    folder_title = folders_map.get(folder_id, f"folder_{folder_id}")
    safe_folder_title = sanitize_filename(folder_title)
    folder_dir = os.path.join(EXPORT_DIR, safe_folder_title)
    os.makedirs(folder_dir, exist_ok=True)

    dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)
    if dash_resp.status_code != 200:
        print(f"❌ Failed to fetch dashboard '{dash_title}' ({dash_uid})")
        continue

    dash_data = dash_resp.json()
    dashboard_json = dash_data.get("dashboard", {})
    file_path = os.path.join(folder_dir, f"{dash_title}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_json, f, indent=2)

    print(f"✅ Exported '{dash_title}' to folder '{folder_title}'")

print("\n🎉 Export completed successfully!")
