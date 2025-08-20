$ErrorActionPreference = "Stop"

$GrafanaURL = "http://localhost:3000"
$ApiToken   = $env:GRAFANA_API_TOKEN

$exportDir = Join-Path (Get-Location) "library-panels"
if (-not (Test-Path $exportDir)) {
  New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching library panels list..."

# 1) Get raw response
$response = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
  Authorization = "Bearer $ApiToken"
}

# 2) Extract panels array from "elements"
$panels = $response.elements
if (-not $panels -or $panels.Count -eq 0) {
  Write-Error "No library panels found in response. Properties available: $($response.PSObject.Properties.Name -join ', ')"
  exit 1
}

Write-Host "Found $($panels.Count) panels. Exporting each to its own file..."

$idx = 0
foreach ($summary in $panels) {
  $idx++

  $uid  = $summary.uid
  if (-not $uid) { $uid = "no_uid_$idx" }

  $name = $summary.name
  if (-not $name) { $name = "panel_$idx" }

  $safeName = ($name -replace '[\\\/:*?"<>|]', '-') -replace '\s+', '_'
  $safeUid  = ($uid  -replace '[\\\/:*?"<>|]', '-') -replace '\s+', '_'

  # Fetch full detail
  $detail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$uid" -Headers @{
    Authorization = "Bearer $ApiToken"
  }

  # Some Grafana builds wrap detail too
  if ($null -ne $detail.result) {
    $panelObj = $detail.result | Select-Object -First 1
  } elseif ($detail -is [System.Array]) {
    $panelObj = $detail | Select-Object -First 1
  } else {
    $panelObj = $detail
  }

  $filePath = Join-Path $exportDir "$safeName-$safeUid.json"
  $panelObj | ConvertTo-Json -Depth 50 | Set-Content -Path $filePath -Encoding utf8

  Write-Host "Saved: $filePath"
}

Write-Host "Done. Files are in: $exportDir"
