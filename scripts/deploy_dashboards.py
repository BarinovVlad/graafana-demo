import os
import json
import requests
from pathlib import Path

# --- Конфигурация Grafana ---
grafana_targets = [
    {"folder": "hostA", "url": "http://localhost:3000", "token": os.environ["GRAFANA_API_TOKEN"]},
    {"folder": "hostB", "url": "http://localhost:3001", "token": os.environ["GRAFANA_API_TOKENV_2"]},
]

def safe_uid(name: str) -> str:
    uid = ''.join(c.lower() if c.isalnum() or c in "-_" else "-" for c in name)
    return uid[:40]

def deploy_dashboard(grafana_url, api_token, folder_uid, dashboard_file):
    with open(dashboard_file, "r", encoding="utf-8") as f:
        try:
            dashboard = json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️ Skipping invalid JSON {dashboard_file}: {e}")
            return

    if "uid" not in dashboard:
        print(f"❌ Dashboard {dashboard_file} missing 'uid'. Skipping.")
        return

    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

    # Удаляем id и version, если есть
    dashboard.pop("id", None)
    dashboard.pop("version", None)

    # Проверяем, существует ли дашборд
    uid = dashboard["uid"]
    resp = requests.get(f"{grafana_url}/api/dashboards/uid/{uid}", headers=headers)
    if resp.status_code == 200:
        print(f"Deleting existing dashboard {dashboard['title']} ({uid})")
        requests.delete(f"{grafana_url}/api/dashboards/uid/{uid}", headers=headers)

    payload = {"dashboard": dashboard, "folderUid": folder_uid, "overwrite": True}
    print(f"Uploading dashboard: {dashboard_file}")
    r = requests.post(f"{grafana_url}/api/dashboards/db", headers=headers, json=payload)
    r.raise_for_status()

def ensure_folder(grafana_url, api_token, folder_name):
    uid = safe_uid(folder_name)
    headers = {"Authorization": f"Bearer {api_token}"}

    # Проверяем, есть ли уже папка
    resp = requests.get(f"{grafana_url}/api/folders/{uid}", headers=headers)
    if resp.status_code == 200:
        print(f"Folder '{folder_name}' exists.")
        return uid

    print(f"Creating folder '{folder_name}'...")
    payload = {"uid": uid, "title": folder_name}
    r = requests.post(f"{grafana_url}/api/folders", headers={**headers, "Content-Type": "application/json"}, json=payload)
    r.raise_for_status()
    return uid

# --- Главный цикл ---
for target in grafana_targets:
    base_folder = Path("dashboards") / target["folder"]
    url = target["url"]
    token = target["token"]

    print(f"\n===== Deploying to Grafana at {url} from folder {base_folder} =====")

    if not base_folder.exists():
        print(f"No dashboards folder for {target['folder']}, skipping.")
        continue

    for client_folder in sorted(base_folder.iterdir()):
        if not client_folder.is_dir():
            continue
        print(f"\n=== Processing client: {client_folder.name} ===")
        folder_uid = ensure_folder(url, token, client_folder.name)

        for dashboard_file in sorted(client_folder.glob("*.json")):
            deploy_dashboard(url, token, folder_uid, dashboard_file)
