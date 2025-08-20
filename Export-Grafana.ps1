$ErrorActionPreference = "Stop"

# --- Settings ---
$GrafanaURL = "http://localhost:3000"
$ApiToken   = $env:GRAFANA_API_TOKEN

# --- Prepare export dir ---
$exportDir = Join-Path (Get-Location) "library-panels"
if (-not (Test-Path $exportDir)) {
  New-Item -ItemType Directory -Path $exportDir | Out-Null
}

Write-Host "Fetching library panels list..."

# --- 1) Get list of library panels ---
$response = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements" -Headers @{
  Authorization = "Bearer $ApiToken"
}

# Normalize to array of summaries
if ($null -ne $response.result) {
  $panels = $response.result
} elseif ($response -is [System.Array]) {
  $panels = $response
} else {
  $panels = @($response)
}

if (-not $panels -or $panels.Count -eq 0) {
  Write-Error "No library panels returned by API."
  exit 1
}

Write-Host "Found $($panels.Count) panels. Exporting each to its own file..."

# --- 2) Export each panel detail to its own file ---
$idx = 0
foreach ($summary in $panels) {
  $idx++

  # Try multiple property names just in case
  $uid  = $summary.uid
  if (-not $uid -and $summary.PSObject.Properties.Name -contains 'elementUid') { $uid = $summary.elementUid }
  if (-not $uid -or [string]::IsNullOrWhiteSpace($uid)) {
    Write-Warning "Skipping item #$idx (no UID found). Properties: $($summary.PSObject.Properties.Name -join ', ')"
    continue
  }

  $name = $summary.name
  if ([string]::IsNullOrWhiteSpace($name)) { $name = "panel_$idx" }

  # Sanitize filename parts
  $safeName = ($name -replace '[\\\/:*?"<>|]', '-') -replace '\s+', '_'
  $safeUid  = ($uid  -replace '[\\\/:*?"<>|]', '-') -replace '\s+', '_'

  # 2a) Fetch detail by UID
  $detail = Invoke-RestMethod -Uri "$GrafanaURL/api/library-elements/$uid" -Headers @{
    Authorization = "Bearer $ApiToken"
  }

  # Some Grafana builds return { result: [ { ..panel.. } ] }
  if ($null -ne $detail.result) {
    $panelObj = $detail.result | Select-Object -First 1
  } elseif ($detail -is [System.Array]) {
    $panelObj = $detail | Select-Object -First 1
  } else {
    $panelObj = $detail
  }

  # Decide what to save: full object preferred (has meta, model, etc.)
  $toSave = $panelObj

  # Final unique file name
  $filePath = Join-Path $exportDir "$safeName-$safeUid.json"

  # Write single panel per file (pretty JSON for readability)
  $json = $toSave | ConvertTo-Json -Depth 50
  Set-Content -Path $filePath -Value $json -Encoding utf8

  Write-Host "Saved: $filePath"
}

Write-Host "Done. Files are in: $exportDir"
