import os
import requests
import json

# ==== SETTINGS ====
GRAFANA_URL = "http://localhost:3000"  # Grafana URL
API_TOKEN = "GRAFANA_API_TOKEN"           # Ваш API токен
OUTPUT_DIR = "exported_dashboards"     # Папка для сохранения JSON
# ==================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Получаем список всех папок
folders_resp = requests.get(f"{GRAFANA_URL}/api/folders", headers=HEADERS)
folders_list = folders_resp.json()

# Добавляем корневую папку "General"
folders_list = [{"uid": "", "title": "General"}] + folders_list

# 2. Для каждой папки получаем дашборды
for folder in folders_list:
    folder_name = folder['title']
    folder_uid = folder['uid'] if folder['uid'] else "general"
    folder_path = os.path.join(OUTPUT_DIR, folder_name.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    # Формируем корректный URL для поиска дашбордов
    if folder_uid == "general":
        search_url = f"{GRAFANA_URL}/api/search?query=&type=dash-db"
    else:
        search_url = f"{GRAFANA_URL}/api/search?folderIds={folder_uid}&type=dash-db"

    search_resp = requests.get(search_url, headers=HEADERS)
    dashboards = search_resp.json()

    for dash in dashboards:
        dash_uid = dash['uid']
        dash_title = dash['title']

        dash_resp = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", headers=HEADERS)
        dash_json = dash_resp.json()['dashboard']

        # Убираем id, чтобы Grafana создавала новый при импорте
        dash_json['id'] = None

        filename = os.path.join(folder_path, f"{dash_title.replace(' ', '_')}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(dash_json, f, indent=2, ensure_ascii=False)

        print(f"Saved dashboard: {folder_name}/{dash_title}")

print("\n✅ Export completed!")
