import os
import json
import requests
import re

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")

if not API_TOKEN:
    raise ValueError("Environment variable GRAFANA_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

EXPORT_DIR = "exported_library_panels"
os.makedirs(EXPORT_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# === GET ALL LIBRARY PANELS ===
def get_library_panels():
    url = f"{GRAFANA_URL}/api/library-panels"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch library panels: {response.status_code} - {response.text}")
    return response.json().get("result", [])

library_panels = get_library_panels()

for panel in library_panels:
    uid = panel["uid"]
    panel_name = sanitize_filename(panel.get("name", uid))
    detail_url = f"{GRAFANA_URL}/api/library-panels/{uid}"
    detail_resp = requests.get(detail_url, headers=HEADERS)
    if detail_resp.status_code != 200:
        print(f"❌ Failed to fetch panel '{panel_name}' ({uid})")
        continue

    panel_data = detail_resp.json()
    file_path = os.path.join(EXPORT_DIR, f"{panel_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(panel_data, f, indent=2)

    print(f"✅ Exported library panel '{panel_name}' -> {file_path}")

print("\n🎉 Export of library panels completed successfully!")
