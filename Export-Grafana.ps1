$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"   # Update if needed
$ApiToken = $env:GRAFANA_API_TOKEN
 # Or replace with your token

# Export directory
$exportDir = "./library-panels"
if (-not (Test-Path $exportDir)) {
  New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching all library panels from Grafana..."

# Get all library panels
$libraryPanels = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
  Authorization = "Bearer $ApiToken"
}

foreach ($panel in $libraryPanels) {
  # Get detailed info for each panel
  $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$($panel.uid)" -Headers @{
    Authorization = "Bearer $ApiToken"
  }

  # File name based on UID
  $fileName = Join-Path $exportDir "LibraryPanel-$($panel.uid).json"

  # Save JSON to file
  $panelDetail | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

  Write-Host "Exported library panel: $fileName"
}

Write-Host "Export complete. Panels saved in $exportDir"
