import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"       # your Grafana URL
API_TOKEN = "GRAFANA_API_TOKEN"               # replace with your API key
OUTPUT_DIR = "exported_dashboards"         # folder to save JSON dashboards
PROVISIONING_FILE = "provisioning/dashboards.yaml"
# ==================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Create output folders
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROVISIONING_FILE), exist_ok=True)

# 1. Get folders from Grafana
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
folders = folders_resp.json()
if not isinstance(folders, list):
    folders = []

# Add root "General" folder
folders.insert(0, {"uid": "", "title": "General"})

# Prepare provisioning entries
provisioning_entries = []

# 2. Export dashboards
for folder in folders:
    folder_name = folder['title']
    folder_uid = folder['uid'] if folder['uid'] else "general"
    folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # Get dashboards in folder
    search_resp = requests.get(
        f"{GRAFANA_URL}/api/search?folderIds={folder_uid}&type=dash-db",
        headers=HEADERS
    )
    dashboards = search_resp.json()

    for dash in dashboards:
        dash_uid = dash['uid']
        dash_title = dash['title']

        dash_resp = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}",
            headers=HEADERS
        )
        dash_json = dash_resp.json()['dashboard']

        # Remove id to allow import as new dashboard
        dash_json['id'] = None

        filename = os.path.join(folder_path, f"{dash_title.replace(' ', '_')}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dash_json, f, indent=2, ensure_ascii=False)

        print(f"Saved dashboard: {folder_name}/{dash_title}")

    # Add entry to provisioning
    provisioning_entries.append({
        "name": folder_name,
        "folder": folder_name if folder_name != "General" else "",
        "type": "file",
        "options": {
            "path": os.path.abspath(folder_path)
        }
    })

# 3. Write provisioning file
with open(PROVISIONING_FILE, "w", encoding="utf-8") as f:
    f.write("apiVersion: 1\n")
    f.write("providers:\n")
    for entry in provisioning_entries:
        f.write(f"  - name: '{entry['name']}'\n")
        f.write(f"    folder: '{entry['folder']}'\n")
        f.write(f"    type: {entry['type']}\n")
        f.write(f"    options:\n")
        f.write(f"      path: {entry['options']['path']}\n")

print("\n✅ Export completed!")
print(f"Provisioning file created: {PROVISIONING_FILE}")
