import os
import json
import requests
import re

# === CONFIG ===
GRAFANA_URL = "http://localhost:3000"   # URL Grafana
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")  # Токен из переменной окружения
EXPORT_DIR = "library-panels"

if not API_TOKEN:
    raise ValueError("❌ Environment variable GRAFANA_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(EXPORT_DIR, exist_ok=True)

def sanitize_filename(name):
    """Удаляем запрещённые символы из имени файла"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def export_library_panels():
    print("Fetching all library panels from Grafana...")

    # Получаем список всех библиотечных панелей
    response = requests.get(f"{GRAFANA_URL}/api/library-elements", headers=HEADERS)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch library panels: {response.status_code} - {response.text}")

    panels = response.json()
    if not isinstance(panels, list):
        raise RuntimeError(f"Unexpected response format: {panels}")

    print(f"Found {len(panels)} library panels")

    for panel in panels:
        # UID и имя панели
        panel_uid = panel.get("uid")
        panel_name = panel.get("name", panel_uid)
        if not panel_uid:
            print("⚠️ Skipping panel with no UID")
            continue

        print(f"Fetching details for panel UID: {panel_uid}")

        # Получаем полные данные панели
        detail_url = f"{GRAFANA_URL}/api/library-elements/{panel_uid}"
        detail_resp = requests.get(detail_url, headers=HEADERS)

        if detail_resp.status_code != 200:
            print(f"⚠️ Skipping panel {panel_uid}, failed to fetch details: {detail_resp.status_code}")
            continue

        panel_data = detail_resp.json()
        filename = os.path.join(EXPORT_DIR, f"{sanitize_filename(panel_name)}-{panel_uid}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(panel_data, f, indent=2)

        print(f"✅ Exported panel: {panel_name} -> {filename}")

    print("\n🎉 Export complete. Panels saved in:", EXPORT_DIR)


if __name__ == "__main__":
    export_library_panels()
