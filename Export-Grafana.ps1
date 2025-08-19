$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"   # Update if needed
$ApiToken = $env:GRAFANA_API_TOKEN

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
    # Extract the main panel object (libraryPanel inside model)
    $libraryPanelData = $panel.model.libraryPanel

    # Create a file name based on UID
    $fileName = Join-Path $exportDir "$($libraryPanelData.uid)-$($libraryPanelData.name).json"

    # Save JSON to file
    $libraryPanelData | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

    Write-Host "Exported library panel: $fileName"
}

Write-Host "Export complete. Panels saved in $exportDir"
