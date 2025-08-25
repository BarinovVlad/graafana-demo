import os
import json
import requests
import re

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"  # поменяй на свой URL
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")

if not API_TOKEN:
    raise ValueError("❌ Environment variable GRAFANA_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

EXPORT_DIR = "library-panels"
os.makedirs(EXPORT_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def export_library_panels():
    print("Fetching all library panels from Grafana...")

    response = requests.get(f"{GRAFANA_URL}/api/library-elements", headers=HEADERS)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch library panels: {response.status_code} - {response.text}")

    panels = response.json().get("result", [])
    print(f"Found {len(panels)} library panels")

    for panel in panels:
        uid = panel.get("uid")
        name = panel.get("name", uid)

        detail_resp = requests.get(f"{GRAFANA_URL}/api/library-elements/{uid}", headers=HEADERS)
        if detail_resp.status_code != 200:
            print(f"⚠️ Skipping panel {uid}, failed to fetch details")
            continue

        panel_data = detail_resp.json()
        panel_only = panel_data.get("result", panel_data)

        filename = os.path.join(EXPORT_DIR, f"{sanitize_filename(name)}-{uid}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(panel_only, f, indent=2)

        print(f"✅ Exported library panel: {name} -> {filename}")

if __name__ == "__main__":
    export_library_panels()
    print("\n🎉 Export completed successfully!")
