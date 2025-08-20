$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"
$ApiToken   = $env:GRAFANA_API_TOKEN

# Export directory
$exportDir = "./library-panels"
if (-not (Test-Path $exportDir)) {
  New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching all library panels from Grafana..."

# 1. Get all library panels (list only)
$libraryPanels = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
  Authorization = "Bearer $ApiToken"
}

foreach ($panel in $libraryPanels) {
  $uid = $panel.uid
  $name = $panel.name -replace '[^\w\-]', '_'  # sanitize filename

  # 2. Get details for each panel by UID
  $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$uid" -Headers @{
    Authorization = "Bearer $ApiToken"
  }

  # 3. Extract the panel object (NOT the array)
  $panelObj = $panelDetail.result[0]

  # 4. Save each panel into its own file
  $fileName = Join-Path $exportDir "$name-$uid.json"
  $panelObj | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

  Write-Host "Exported panel: $fileName"
}

Write-Host "✅ Done. Panels saved separately in $exportDir"
