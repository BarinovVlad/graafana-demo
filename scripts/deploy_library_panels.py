import os
import json
import requests
from pathlib import Path


GRAFANA_TARGETS = [
    {"url": os.environ.get("GRAFANA_HOST_A", "http://localhost:3000"), "token": os.environ.get("GRAFANA_API_TOKEN")},
    {"url": os.environ.get("GRAFANA_HOST_B", "http://localhost:3001"), "token": os.environ.get("GRAFANA_API_TOKENV_2")}
]

BASE_FOLDER = Path("./provisioning/library_panels")
PER_PAGE = 500

if not BASE_FOLDER.exists():
    print("No library panels folder found. Skipping.")
    exit(0)


def get_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def fetch_panel(url, token, uid):
    try:
        resp = requests.get(f"{url}/api/library-elements/{uid}", headers=get_headers(token), timeout=30)
        if resp.status_code == 200:
            return resp.json().get("result")
    except Exception as e:
        print(f"Error fetching {uid}: {e}")
    return None


def create_panel(url, token, uid, name, model):
    payload = {"uid": uid, "name": name, "kind": 1, "model": model}
    print(f"Creating library panel '{name}' (uid={uid})...")
    resp = requests.post(f"{url}/api/library-elements", headers=get_headers(token), json=payload, timeout=30)
    if resp.status_code not in (200, 202):
        print(f"Failed to create {uid}: {resp.status_code} {resp.text}")
    resp.raise_for_status()


def update_panel(url, token, uid, name, model, version):
    payload = {"uid": uid, "name": name, "kind": 1, "model": model, "version": version}
    try:
        print(f"Updating library panel '{name}' (uid={uid}, version={version})...")
        resp = requests.patch(f"{url}/api/library-elements/{uid}", headers=get_headers(token), json=payload, timeout=30)

        if resp.status_code == 412:
            
            print(f"Version mismatch for {uid}; refetching...")
            fresh = fetch_panel(url, token, uid)
            if fresh:
                payload["version"] = fresh.get("version")
                resp = requests.patch(f"{url}/api/library-elements/{uid}", headers=get_headers(token), json=payload, timeout=30)
        return resp
    except Exception as e:
        print(f"Failed to update {uid}: {e}")
        raise


def get_remote_panels(url, token):
    remote = []
    page = 1
    while True:
        resp = requests.get(
            f"{url}/api/library-elements?kind=1&perPage={PER_PAGE}&page={page}",
            headers=get_headers(token),
            timeout=30
        )
        resp.raise_for_status()
        res_json = resp.json().get("result", {})
        remote.extend(res_json.get("elements", []))
        if len(remote) >= res_json.get("totalCount", 0):
            break
        page += 1
    return remote


def get_connections(url, token, uid):
    try:
        resp = requests.get(f"{url}/api/library-elements/{uid}/connections", headers=get_headers(token), timeout=30)
        if resp.status_code == 200:
            result = resp.json().get("result")
            return result if isinstance(result, list) else []
    except Exception as e:
        print(f"Error fetching connections for {uid}: {e}")
    return []


def delete_panel(url, token, uid, name):
    print(f"Deleting library panel '{name}' (uid={uid})...")
    resp = requests.delete(f"{url}/api/library-elements/{uid}", headers=get_headers(token), timeout=30)
    if resp.status_code in (200, 202):
        print(f"Deleted '{name}' uid={uid}")
    elif resp.status_code == 404:
        print(f"Panel '{name}' uid={uid} already deleted.")
    else:
        print(f"Failed to delete '{name}' uid={uid}: {resp.status_code} {resp.text}")


def deploy_library_panels():
    for target in GRAFANA_TARGETS:
        url, token = target["url"], target["token"]
        if not token:
            print(f"Skipping {url}: no token provided.")
            continue

        print(f"\n===== Deploying library panels to {url} =====")

        local_uids = []

        
        for json_file in BASE_FOLDER.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            panel_data = data.get("result", data)
            if not panel_data.get("uid"):
                raise ValueError(f"Library panel '{json_file.name}' missing 'uid'.")
            if not panel_data.get("model"):
                raise ValueError(f"Library panel '{json_file.name}' missing 'model'.")

            uid = panel_data["uid"]
            name = panel_data.get("name") or panel_data["model"].get("title") or json_file.stem
            model = panel_data["model"]

            local_uids.append(uid)

            existing = fetch_panel(url, token, uid)
            if existing:
                version = existing.get("version")
                update_panel(url, token, uid, name, model, version)
            else:
                create_panel(url, token, uid, name, model)

   
        remote_panels = get_remote_panels(url, token)
        to_delete = [p for p in remote_panels if p["uid"] not in local_uids]

        for panel in to_delete:
            uid, name = panel["uid"], panel.get("name", panel["uid"])
            connections = get_connections(url, token, uid)
            if connections:
                print(f"Skip delete '{name}' uid={uid}: in use ({len(connections)} connections).")
                continue
            delete_panel(url, token, uid, name)


if __name__ == "__main__":
    deploy_library_panels()
