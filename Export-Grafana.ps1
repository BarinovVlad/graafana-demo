$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"
$ApiToken   = $env:GRAFANA_API_TOKEN

# Export directory
$exportDir = "./library-panels"
if (-not (Test-Path $exportDir)) {
  New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching all library panels from Grafana..."

# Get list of panels
$libraryPanels = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
  Authorization = "Bearer $ApiToken"
}

foreach ($panel in $libraryPanels) {
  $uid = $panel.uid
  $name = $panel.name -replace '[^\w\-]', '_'  # sanitize filename

  # Get details for each panel
  $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$uid" -Headers @{
    Authorization = "Bearer $ApiToken"
  }

  # File name: PanelName-UID.json
  $fileName = Join-Path $exportDir "$name-$uid.json"

  # Save as JSON
  $panelDetail | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

  Write-Host "Exported: $fileName"
}

Write-Host "✅ Export complete. Files saved in $exportDir"
