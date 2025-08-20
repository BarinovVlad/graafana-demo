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

  # Extract the actual panel object (first element of result array)
  $panelObj = $panelDetail.result[0]

  # File per panel
  $fileName = Join-Path $exportDir "$name-$uid.json"

  # Save JSON nicely formatted
  $panelObj | ConvertTo-Json -Depth 20 | Set-Content -Path $fileName -Encoding utf8

  Write-Host "Exported: $fileName"
}

Write-Host "✅ Export complete. Each panel saved separately in $exportDir"
