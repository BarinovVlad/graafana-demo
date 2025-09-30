import os
import json
import requests
from pathlib import Path

# === CONFIG ===
GRAFANA_TARGETS = [
    {"url": os.environ.get("GRAFANA_HOST_A", "http://localhost:3000"), "token": os.environ.get("GRAFANA_API_TOKEN")},
    {"url": os.environ.get("GRAFANA_HOST_B", "http://localhost:3001"), "token": os.environ.get("GRAFANA_API_TOKENV_2")}
]

DATASOURCE_MAP = {
    "http://localhost:3000": {"prometheus": "ceu6ho1muemm8a"},
    "http://localhost:3001": {"prometheus": "aeu6eea0zjdvke"}
}

BASE_FOLDER = Path("./provisioning/library_panels")
PER_PAGE = 500

if not BASE_FOLDER.exists():
    print("No library panels folder found. Skipping.")
    exit(0)

def sanitize_panel_model(panel_model, grafana_url):
    # Обновляем datasource.uid согласно карте
    targets = panel_model.get("targets", [])
    for t in targets:
        ds = t.get("datasource")
        if isinstance(ds, dict) and "type" in ds:
            ds_type = ds["type"]
            if DATASOURCE_MAP.get(grafana_url, {}).get(ds_type):
                t["datasource"]["uid"] = DATASOURCE_MAP[grafana_url][ds_type]
    return panel_model

def deploy_library_panels():
    for target in GRAFANA_TARGETS:
        url = target["url"]
        token = target["token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        print(f"\n===== Deploying library panels to {url} =====")

        local_uids = []

        # === Process local JSON files ===
        for json_file in BASE_FOLDER.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            panel_data = data.get("result", data)
            if not panel_data.get("uid"):
                raise ValueError(f"Library panel '{json_file.name}' missing 'uid'.")
            if not panel_data.get("model"):
                raise ValueError(f"Library panel '{json_file.name}' missing 'model'.")

            panel_uid = panel_data["uid"]
            panel_name = panel_data.get("name") or panel_data["model"].get("title") or json_file.stem
            local_uids.append(panel_uid)

            panel_data["model"] = sanitize_panel_model(panel_data["model"], url)

            # === Check if panel exists ===
            existing = None
            try:
                resp = requests.get(f"{url}/api/library-elements/{panel_uid}", headers=headers, timeout=30)
                resp.raise_for_status()
                existing = resp.json().get("result")
            except requests.exceptions.HTTPError:
                pass

            if existing:
                version = existing["version"]
                payload = {
                    "uid": panel_uid,
                    "name": panel_name,
                    "kind": 1,
                    "model": panel_data["model"],
                    "version": version
                }
                try:
                    print(f"Updating library panel '{panel_name}' (uid: {panel_uid})...")
                    requests.patch(f"{url}/api/library-elements/{panel_uid}", headers=headers, json=payload, timeout=30)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 412:
                        print(f"Version mismatch for {panel_uid}; refetching...")
                        fresh = requests.get(f"{url}/api/library-elements/{panel_uid}", headers=headers, timeout=30).json()["result"]
                        payload["version"] = fresh["version"]
                        requests.patch(f"{url}/api/library-elements/{panel_uid}", headers=headers, json=payload, timeout=30)
                    else:
                        raise
            else:
                payload = {
                    "uid": panel_uid,
                    "name": panel_name,
                    "kind": 1,
                    "model": panel_data["model"]
                }
                print(f"Creating library panel '{panel_name}' (uid: {panel_uid})...")
                requests.post(f"{url}/api/library-elements", headers=headers, json=payload, timeout=30)

        # === Delete remote panels not present locally ===
        remote_panels = []
        page = 1
        while True:
            resp = requests.get(f"{url}/api/library-elements?kind=1&perPage={PER_PAGE}&page={page}", headers=headers, timeout=30)
            resp.raise_for_status()
            res_json = resp.json()["result"]
            remote_panels.extend(res_json.get("elements", []))
            if len(remote_panels) >= res_json.get("totalCount", 0):
                break
            page += 1

        to_delete = [p for p in remote_panels if p["uid"] not in local_uids]

        for panel in to_delete:
            conn_resp = requests.get(f"{url}/api/library-elements/{panel['uid']}/connections", headers=headers, timeout=30)
            connections = conn_resp.json().get("result", [])
            if connections:
                print(f"Skip delete '{panel['name']}' uid={panel['uid']}: in use ({len(connections)} connections).")
                continue
            print(f"Deleting library panel '{panel['name']}' uid={panel['uid']}...")
            requests.delete(f"{url}/api/library-elements/{panel['uid']}", headers=headers, timeout=30)

if __name__ == "__main__":
    deploy_library_panels()

