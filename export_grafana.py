import os
import json
import requests

# Config
GRAFANA_URL = "http://localhost:3000"
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")  

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

EXPORT_DIR = "exported_dashboards"


os.makedirs(EXPORT_DIR, exist_ok=True)


folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
if folders_resp.status_code != 200:
    print("Unexpected folders response:", folders_resp.json())
    folders_list = []
else:
    folders_list = folders_resp.json()


for folder in folders_list:
    folder_uid = folder['uid']
    folder_title = folder['title']
    folder_dir = os.path.join(EXPORT_DIR, folder_title)
    os.makedirs(folder_dir, exist_ok=True)

    
    search_resp = requests.get(
       f"{GRAFANA_URL}/api/search?type=dash-db&folderIds={folder_uid}",
        headers=HEADERS
    )

    if search_resp.status_code != 200:
        print(f"Unexpected dashboards response for folder {folder_title}:", search_resp.json())
        continue

    dashboards = search_resp.json()
    if not dashboards:
        print(f"No dashboards found in folder {folder_title}")
        continue

    for dash in dashboards:
        dash_uid = dash['uid']
        dash_title = dash['title']
        dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)

        if dash_resp.status_code != 200:
            print(f"Failed to get dashboard {dash_title} ({dash_uid})")
            continue

        dash_data = dash_resp.json()
       
        dashboard_json = dash_data.get("dashboard", {})
        file_name = f"{dash_title}.json".replace("/", "_")  
        file_path = os.path.join(folder_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dashboard_json, f, indent=2)

print("\n✅ Export completed!")
