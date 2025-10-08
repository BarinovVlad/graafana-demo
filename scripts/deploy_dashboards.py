import os
import json
import requests
from pathlib import Path

# === CONFIG ===
GRAFANA_TARGETS = [
    {
        "folder": "hostB",
        "url": "http://localhost:3001",
        "token": os.environ.get("GRAFANA_API_TOKENV_2"),
    }
]

BASE_DIR = Path("dashboards")


def safe_uid(name: str) -> str:
    """Generate safe folder uid (lowercase, only a-z0-9 and '-')"""
    uid = "".join(c if c.isalnum() or c in "-_" else "-" for c in name.lower())
    return uid[:40]


def grafana_get(url, token):
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def grafana_post(url, token, payload):
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def grafana_delete(url, token):
    resp = requests.delete(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if resp.status_code not in (200, 202, 404):
        resp.raise_for_status()
    return resp.json() if resp.text else None


def ensure_folder(base_url, token, folder_name):
    uid = safe_uid(folder_name)
    folder = grafana_get(f"{base_url}/api/folders/{uid}", token)
    if folder:
        print(f"Folder '{uid}' exists.")
        return uid, folder["id"]

    print(f"Creating folder '{uid}'...")
    payload = {"uid": uid, "title": folder_name}
    folder = grafana_post(f"{base_url}/api/folders", token, payload)
    return uid, folder["id"]


def deploy_dashboards(base_url, token, client_folder: Path):
    folder_uid, folder_id = ensure_folder(base_url, token, client_folder.name)
    local_uids = []

    for file in client_folder.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            dashboard = json.load(f)

        if "uid" not in dashboard:
            raise ValueError(f"Dashboard '{file.name}' missing 'uid'.")

        local_uids.append(dashboard["uid"])

        # Remove unwanted fields
        dashboard.pop("id", None)
        dashboard.pop("version", None)

        existing = grafana_get(f"{base_url}/api/dashboards/uid/{dashboard['uid']}", token)
        if existing:
            print(f"Dashboard '{dashboard['title']}' exists. Deleting old version...")
            grafana_delete(f"{base_url}/api/dashboards/uid/{dashboard['uid']}", token)

        payload = {"dashboard": dashboard, "folderUid": folder_uid, "overwrite": True}
        print(f"Uploading dashboard: {file.name}")
        grafana_post(f"{base_url}/api/dashboards/db", token, payload)

    # cleanup: delete dashboards not in repo
    all_dashboards = grafana_get(f"{base_url}/api/search?query=&type=dash-db", token)
    folder_dashboards = [d for d in all_dashboards if d.get("folderId") == folder_id]
    to_delete = [d for d in folder_dashboards if d["uid"] not in local_uids]

    for dash in to_delete:
        print(f"Deleting dashboard '{dash['title']}' (uid: {dash['uid']})...")
        grafana_delete(f"{base_url}/api/dashboards/uid/{dash['uid']}", token)


def cleanup_folders(base_url, token, git_folders):
    grafana_folders = grafana_get(f"{base_url}/api/folders", token)
    git_uids = [safe_uid(f.name) for f in git_folders]

    for folder in grafana_folders:
        uid = safe_uid(folder["title"])
        if uid not in git_uids:
            print(f"Folder '{uid}' not found in Git. Deleting...")

            all_dashboards = grafana_get(f"{base_url}/api/search?query=&type=dash-db", token)
            dashboards_in_folder = [d for d in all_dashboards if d.get("folderId") == folder["id"]]

            for dash in dashboards_in_folder:
                print(f"Deleting dashboard '{dash['title']}' (uid: {dash['uid']})...")
                grafana_delete(f"{base_url}/api/dashboards/uid/{dash['uid']}", token)

            grafana_delete(f"{base_url}/api/folders/{uid}", token)
            print(f"Folder '{uid}' deleted.")


def main():
    for target in GRAFANA_TARGETS:
        folder = target["folder"]
        url = target["url"]
        token = target["token"]

        base_folder = BASE_DIR / folder
        print(f"\n===== Deploying to Grafana at {url} from folder {base_folder} =====")

        if not base_folder.exists():
            print(f"No dashboards found in {base_folder}")
            continue

        git_folders = [f for f in base_folder.iterdir() if f.is_dir()]
        if not git_folders:
            print(f"No subfolders found in {base_folder}")
            continue

        for client_folder in git_folders:
            print(f"\n=== Processing client: {client_folder.name} ===")
            deploy_dashboards(url, token, client_folder)

        cleanup_folders(url, token, git_folders)


if __name__ == "__main__":
    main()
