import os
import json
import requests
import re

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")
EXPORT_DIR = "library-panels"

if not API_TOKEN:
    raise ValueError("❌ Environment variable GRAFANA_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(EXPORT_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def export_library_panels():
    print("Fetching all library panels from Grafana...")

    response = requests.get(f"{GRAFANA_URL}/api/library-elements", headers=HEADERS)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch library panels: {response.status_code} - {response.text}")

    data = response.json()
    panels = data.get("result", {}).get("elements", [])
    print(f"Found {len(panels)} library panels")

    for panel in panels:
        uid = panel.get("uid")
        name = panel.get("name", uid)
        if not uid:
            print("⚠️ Skipping panel with no UID")
            continue

        print(f"Fetching details for panel UID: {uid}")
        detail_resp = requests.get(f"{GRAFANA_URL}/api/library-elements/{uid}", headers=HEADERS)

        if detail_resp.status_code != 200:
            print(f"⚠️ Skipping panel {uid}, failed to fetch details: {detail_resp.status_code}")
            continue

        panel_data = detail_resp.json()
        filename = os.path.join(EXPORT_DIR, f"{sanitize_filename(name)}-{uid}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(panel_data, f, indent=2)

        print(f"✅ Exported panel: {name} -> {filename}")

    print("\n🎉 Export complete. Panels saved in:", EXPORT_DIR)

if __name__ == "__main__":
    export_library_panels()
