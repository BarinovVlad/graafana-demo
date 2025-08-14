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

# === UTILS ===
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# === GET FOLDERS ===
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
if folders_resp.status_code != 200:
    print("❌ Failed to fetch folders:", folders_resp.text)
    folders_list = []
else:
    folders_list = folders_resp.json()

# Add default "General" folder manually
folders_list.append({
    "id": 0,
    "title": "General"
})

# === EXPORT DASHBOARDS ===
exported_uids = set()

for folder in folders_list:
    folder_id = folder["id"]
    folder_title = sanitize_filename(folder["title"])
    folder_dir = os.path.join(EXPORT_DIR, folder_title)
    os.makedirs(folder_dir, exist_ok=True)

    search_url = f"{GRAFANA_URL}/api/search?type=dash-db&folderIds={folder_id}"
    search_resp = requests.get(search_url, headers=HEADERS)

    if search_resp.status_code != 200:
        print(f"❌ Failed to fetch dashboards for folder '{folder_title}':", search_resp.text)
        continue

    dashboards = search_resp.json()
    if not dashboards:
        print(f"ℹ️ No dashboards found in folder '{folder_title}'")
        continue
    for dash in dashboards:
        dash_uid = dash["uid"]
        dash_title = sanitize_filename(dash["title"])

        if dash_uid in exported_uids:
            continue  # Skip already exported dashboards

        dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)
        if dash_resp.status_code != 200:
            print(f"❌ Failed to fetch dashboard '{dash_title}' ({dash_uid})")
            continue

        dash_data = dash_resp.json()
        dashboard_json = dash_data.get("dashboard", {})
        file_path = os.path.join(folder_dir, f"{dash_title}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dashboard_json, f, indent=2)

        exported_uids.add(dash_uid)
        print(f"✅ Exported '{dash_title}' to '{folder_title}'")

print("\n🎉 Export completed successfully!")
