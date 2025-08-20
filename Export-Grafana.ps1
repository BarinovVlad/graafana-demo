$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"
$ApiToken   = $env:GRAFANA_API_TOKEN

# Export directory
$exportDir = "./library-panels"
if (-not (Test-Path $exportDir)) {
  New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching all library panels from Grafana..."

# Get all library panels (list)
$libraryPanels = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
  Authorization = "Bearer $ApiToken"
}

foreach ($panel in $libraryPanels) {
  $uid = $panel.uid
  $name = $panel.name -replace '[^\w\-]', '_'  # sanitize filename

  # Get panel detail by UID
  $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$uid" -Headers @{
    Authorization = "Bearer $ApiToken"
  }

  # Each panel in its own file
  $fileName = Join-Path $exportDir "$name-$uid.json"

  # Save JSON for THIS panel only
  $json = $panelDetail | ConvertTo-Json -Depth 20 -Compress
  Set-Content -Path $fileName -Value $json -Encoding utf8

  Write-Host "Exported: $fileName"
}

Write-Host "✅ Export complete. Each panel saved separately in $exportDir"
