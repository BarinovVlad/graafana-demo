$ErrorActionPreference = "Stop"

# Grafana settings
$GrafanaURL = "http://localhost:3000"   # Update if needed
$ApiToken = $env:GRAFANA_API_TOKEN      

# Base export directory
$exportBaseDir = "./library-panels"
if (-not (Test-Path $exportBaseDir)) {
    New-Item -ItemType Directory -Path $exportBaseDir | Out-Null
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

    # Determine folder name from panel metadata
    $folderName = if ($panelDetail.meta.folderName) { $panelDetail.meta.folderName } else { "default" }

    # Create folder if it doesn't exist
    $folderPath = Join-Path $exportBaseDir $folderName
    if (-not (Test-Path $folderPath)) {
        New-Item -ItemType Directory -Path $folderPath | Out-Null
    }

    # File name based on UID
    $fileName = Join-Path $folderPath "LibraryPanel-$($panelDetail.uid).json"

    # Save JSON to file
    $panelDetail | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

    Write-Host "Exported library panel: $fileName"
}

Write-Host "Export complete. Panels saved in $exportBaseDir"
