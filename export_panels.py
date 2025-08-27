import os
import json
import requests
import re

# === CONFIG ===
GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")
API_TOKEN = os.environ.get("GRAFANA_API_TOKEN")
EXPORT_DIR = "library-panels"

if not API_TOKEN:
    raise ValueError("Environment variable GRAFANA_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(EXPORT_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def transform_panel(panel):
    """Преобразуем панель к push-ready формату"""
    panel_copy = panel.copy()
    model = panel_copy.get("model", {})

    # Обновляем datasource в targets
    targets = model.get("targets", [])
    for t in targets:
        if isinstance(t.get("datasource"), str):
            t["datasource"] = {"type": "prometheus", "uid": t["datasource"]}

    # Если сам datasource задан строкой, приводим к объекту
    if isinstance(model.get("datasource"), str):
        model["datasource"] = {"type": "prometheus", "uid": model["datasource"]}

    panel_copy["model"] = model

    # Удаляем лишние поля
    for key in ["id", "version", "orgId", "folderId", "meta"]:
        panel_copy.pop(key, None)

    return panel_copy

def export_library_panels():
    print("Fetching all library panels from Grafana...")
    resp = requests.get(f"{GRAFANA_URL}/api/library-elements", headers=HEADERS)
    resp.raise_for_status()
    panels = resp.json().get("result", {}).get("elements", [])
    print(f"Found {len(panels)} library panels")

    for panel in panels:
        uid = panel.get("uid")
        name = panel.get("name") or uid
        if not uid:
            print("Skipping panel with no UID")
            continue

        print(f"Fetching details for panel UID: {uid}")
        detail_resp = requests.get(f"{GRAFANA_URL}/api/library-elements/{uid}", headers=HEADERS)
        detail_resp.raise_for_status()
        panel_data = detail_resp.json().get("result")
        if not panel_data:
            print(f"Skipping panel {uid}, no data in 'result'")
            continue

        transformed = transform_panel(panel_data)
        filename = os.path.join(EXPORT_DIR, f"{sanitize_filename(name)}-{uid}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(transformed, f, indent=2)
        print(f"Exported panel: {name} -> {filename}")

    print(f"\nExport complete. Panels saved in: {EXPORT_DIR}")

if __name__ == "__main__":
    export_library_panels()
