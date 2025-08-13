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
        headers=HEADER

