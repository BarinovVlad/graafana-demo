import os
import json
import requests

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"  # change to your Grafana URL
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")
EXPORT_DIR = "library-panels"

if not API_TOKEN:
    raise ValueError("Environment variable GRAFANA_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(EXPORT_DIR, exist_ok=True)

# === FETCH ALL LIBRARY PANELS ===
def export_library_panels():
    url_all = f"{GRAFANA_URL}/api/library-elements"
    resp = requests.get(url_all, headers=HEADERS)

    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch library panels: {resp.status_code} - {resp.text}")

    library_panels = resp.json()
    print(f"Found {len(library_panels)} library panels")

    for panel in library_panels:
        uid = panel["uid"]
        url_detail = f"{GRAFANA_URL}/api/library-elements/{uid}"
        detail_resp = requests.get(url_detail, headers=HEADERS)
        if detail_resp.status_code != 200:
            print(f"⚠️ Skipping panel {uid}, failed to fetch details")
            continue

        panel_data = detail_resp.json()
        file_path = os.path.join(EXPORT_DIR, f"LibraryPanel-{uid}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(panel_data, f, indent=2)

        print(f"✅ Exported library panel: {file_path}")

if __name__ == "__main__":
    export_library_panels()
