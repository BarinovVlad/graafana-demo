import os
import json
import requests

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"  # Change to your Grafana URL
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")  # Make sure this environment variable is set

if not API_TOKEN:
    raise ValueError("❌ Environment variable GRAFANA_API_TOKEN is not set.")

EXPORT_DIR = "exported_library_panels"
os.makedirs(EXPORT_DIR, exist_ok=True)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# === EXPORT LIBRARY PANELS ===
def export_library_panels():
    # Step 1: fetch all library panel UIDs
    url = f"{GRAFANA_URL}/api/library-elements"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch library panels: {response.status_code} - {response.text}")

    panels = response.json()  # this is a list of panel UIDs
    print(f"Found {len(panels)} library panels")

    # Step 2: fetch each panel detail and save to file
    for panel_uid in panels:
        detail_url = f"{GRAFANA_URL}/api/library-elements/{panel_uid}"
        detail_resp = requests.get(detail_url, headers=HEADERS)

        if detail_resp.status_code != 200:
            print(f"⚠️ Skipping panel {panel_uid}, failed to fetch details")
            continue

        panel_data = detail_resp.json()
        filename = os.path.join(EXPORT_DIR, f"{panel_uid}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(panel_data, f, indent=2)

        print(f"✅ Exported library panel -> {filename}")


if __name__ == "__main__":
    export_library_panels()
    print("\n🎉 Export completed successfully!")
