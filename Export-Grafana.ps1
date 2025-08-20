$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"
$ApiToken = $env:GRAFANA_API_TOKEN

# Путь к JSON с библиотечными панелями
$libraryPanelsFile = "./provisioning/library_panels/library-panels.json"

if (-not (Test-Path $libraryPanelsFile)) {
    Write-Error "Library panels file not found: $libraryPanelsFile"
    exit 1
}

# Читаем все панели из одного файла
$allPanels = Get-Content $libraryPanelsFile -Raw | ConvertFrom-Json

foreach ($panel in $allPanels) {
    # Проверяем наличие uid
    if (-not $panel.uid) {
        Write-Warning "Panel missing uid, skipping"
        continue
    }

    # Удаляем id и version чтобы Grafana приняла панель
    if ($panel.PSObject.Properties.Name -contains 'id') { $panel.PSObject.Properties.Remove('id') }
    if ($panel.PSObject.Properties.Name -contains 'version') { $panel.PSObject.Properties.Remove('version') }

    $payload = @{
        dashboard = $panel
        overwrite = $true
    } | ConvertTo-Json -Depth 20

    # Отправляем на Grafana API
    Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Method Post -Headers @{
        Authorization = "Bearer $ApiToken"
        "Content-Type" = "application/json"
    } -Body $payload

    Write-Host "Deployed library panel: $($panel.title) ($($panel.uid))"
}

Write-Host "All library panels deployed successfully."
