$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"
$ApiToken = $env:GRAFANA_API_TOKEN

$exportDir = "./library-panels"
if (-not (Test-Path $exportDir)) { New-Item -ItemType Directory -Path $exportDir | Out-Null }

Write-Host "Fetching library panels..."

$response = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
    Authorization = "Bearer $ApiToken"
}

# Determine if response is an array or object
$panels = @()
if ($response -is [System.Collections.IEnumerable] -and $response.Count -gt 0) {
    $panels = $response
} elseif ($response.elements -ne $null) {
    $panels = $response.elements
} else {
    Write-Host "No library panels found."
    exit
}

foreach ($panel in $panels) {
    if (-not $panel.uid) { Write-Warning "Skipping a panel with no UID"; continue }

    $panelDetail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$($panel.uid)" -Headers @{
        Authorization = "Bearer $ApiToken"
    }

    $safeName = ($panel.name -replace '[\\/:*?"<>|]', '_')
    $fileName = Join-Path $exportDir "LibraryPanel-$safeName-$($panel.uid).json"

    $panelDetail | ConvertTo-Json -Depth 20 | Out-File -FilePath $fileName -Encoding utf8
    Write-Host "Exported: $fileName"
}

Write-Host "Done. Panels saved in $exportDir"
