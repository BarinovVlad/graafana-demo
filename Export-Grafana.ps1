$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"   # Update if needed
$ApiToken = $env:GRAFANA_API_TOKEN

# Export directory
$exportDir = "./library-panels"
if (-not (Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching all library panels from Grafana..."

# Get all library elements
$response = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
    Authorization = "Bearer $ApiToken"
}

# Check if 'elements' field exists
if ($null -eq $response.elements) {
    Write-Host "No library panels found in Grafana."
    exit
}

foreach ($panel in $response.elements) {
    if ($null -eq $panel.uid) {
        Write-Warning "Skipping a panel with no UID"
        continue
    }

    # Get details for each panel
    $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$($panel.uid)" -Headers @{
        Authorization = "Bearer $ApiToken"
    }

    # Create file name based on UID and panel name
    $safeName = ($panel.name -replace '[\\/:*?"<>|]', '_')
    $fileName = Join-Path $exportDir "LibraryPanel-$safeName-$($panel.uid).json"

    # Save each panel to a separate JSON file
    $panelDetail | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

    Write-Host "Exported library panel: $fileName"
}

Write-Host "Export complete. Panels saved in $exportDir"
