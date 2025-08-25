import os
import json
import requests

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"   # change to your Grafana URL
API_TOKEN = "GRAFANA_API_TOKEN"            # put your Grafana API token here
EXPORT_DIR = "git/library-panels"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# === EXPORT LIBRARY PANELS ===
def export_library_panels():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    url = f"{GRAFANA_URL}/api/library-panels"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch library panels: {response.status_code} - {response.text}")

    panels = response.json().get("result", [])
    print(f"Found {len(panels)} library panels")

    for panel in panels:
        uid = panel["uid"]
        detail_url = f"{GRAFANA_URL}/api/library-panels/{uid}"
        detail_resp = requests.get(detail_url, headers=HEADERS)
        if detail_resp.status_code != 200:
            print(f"⚠️ Skipping panel {uid}, failed to fetch details")
            continue

        panel_data = detail_resp.json()
        filename = os.path.join(EXPORT_DIR, f"{uid}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(panel_data, f, indent=2)
        print(f"✅ Exported {panel['name']} -> {filename}")


# === IMPORT LIBRARY PANELS ===
def import_library_panels():
    for file in os.listdir(EXPORT_DIR):
        if not file.endswith(".json"):
            continue
        filepath = os.path.join(EXPORT_DIR, file)
        with open(filepath, "r", encoding="utf-8") as f:
            panel_data = json.load(f)

        url = f"{GRAFANA_URL}/api/library-panels"
        response = requests.post(url, headers=HEADERS, json=panel_data)

        if response.status_code not in (200, 201):
            print(f"⚠️ Failed to import {file}: {response.status_code} - {response.text}")
        else:
            print(f"✅ Imported {file}")


if __name__ == "__main__":
    mode = input("Choose mode: [e]xport or [i]mport: ").strip().lower()
    if mode == "e":
        export_library_panels()
    elif mode == "i":
        import_library_panels()
    else:
        print("Unknown mode")


