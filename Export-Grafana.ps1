$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"   # URL Grafana
$ApiToken = $env:GRAFANA_API_TOKEN

# Директория для сохранения панелей
$exportDir = "./library-panels"
if (-not (Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching all library panels from Grafana..."

# Получаем список всех библиотечных панелей
$libraryPanels = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
    Authorization = "Bearer $ApiToken"
}

foreach ($panel in $libraryPanels) {
    # Получаем детальную информацию по каждой панели
    $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$($panel.uid)" -Headers @{
        Authorization = "Bearer $ApiToken"
    }

    # Создаем уникальное имя файла для каждой панели
    $safeName = ($panelDetail.title -replace '[^\w\d_-]', '_')  # заменяем запрещенные символы
    $fileName = Join-Path $exportDir "$safeName-$($panel.uid).json"

    # Сохраняем JSON в отдельный файл
    $panelDetail | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

    Write-Host "Exported library panel: $fileName"
}

Write-Host "Export complete. Panels saved in $exportDir"
