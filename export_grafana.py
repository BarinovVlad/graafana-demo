import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"  # Grafana URL
API_TOKEN = "GRAFANA_API_TOKEN"           # Your Grafana API key
OUTPUT_DIR = "exported_dashboards"     # Where dashboards will be saved
# ==================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Get all folders
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
folders = folders_resp.json()

# Add root folder (for dashboards without folder)
folders.insert(0, {"uid": "", "title": "General"})

for folder in folders:
    folder_name = folder['title']
    folder_uid = folder['uid'] if folder['uid'] else "general"
    folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # Get dashboards in the folder
    search_resp = requests.get(
        f"{GRAFANA_URL}/api/search?query=&type=dash-db&folderIds={folder_uid}",
        headers=HEADERS
    )
    dashboar
