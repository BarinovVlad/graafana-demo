$ErrorActionPreference = "Stop"

# Путь к файлу с библиотечными панелями
$libraryFile = "./provisioning/library_panels/library-panels.json"

# Папка для раздельных файлов
$exportDir = "./provisioning/library_panels/split"
if (-not (Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir | Out-Null
}

# Читаем массив панелей
$allPanels = Get-Content $libraryFile -Raw | ConvertFrom-Json

foreach ($panel in $allPanels) {
    if (-not $panel.uid) {
        Write-Warning "Panel missing uid, skipping"
        continue
    }

    $fileName = Join-Path $exportDir ("LibraryPanel-" + $panel.uid + ".json")
    $panel | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

    Write-Host "Exported panel: $fileName"
}

Write-Host "All panels exported successfully!"
