$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"
$ApiToken = $env:GRAFANA_API_TOKEN

$exportBaseDir = "./library-panels"
if (-not (Test-Path $exportBaseDir)) {
    New-Item -ItemType Directory -Path $exportBaseDir | Out-Null
}

Write-Host "Fetching all library panels from Grafana..."

# Get all library panels
$response = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
    Authorization = "Bearer $ApiToken"
}

# Check if response is an array
if ($response -is [System.Array]) {
    $panels = $response
} else {
    $panels = @($response)
}

foreach ($panel in $panels) {
    # Get detailed info for each panel
    $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$($panel.uid)" -Headers @{
        Authorization = "Bearer $ApiToken"
    }

    # File name based on UID
    $fileName = Join-Path $exportBaseDir "LibraryPanel-$($panelDetail.uid).json"

    # Save JSON to file
    $panelDetail | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8

    Write-Host "Exported library panel: $fileName"
}

Write-Host "Export complete. Panels saved in $exportBaseDir"
