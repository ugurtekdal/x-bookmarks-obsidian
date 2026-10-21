<#
  bookmarks-sync.ps1
  ------------------
  Downloads X bookmarks with birdmarks and copies only the NEW ones (optionally only from selected
  X bookmark folders) into the "pending" folder. Turning them into notes and writing them to the vault
  is done by the /x-bookmarks skill in Claude Code.

  Settings come from the same config.json the Python scripts use
  ($env:X_BOOKMARKS_CONFIG, otherwise ~/.x-bookmarks/config.json).

  Usage:
    .\bookmarks-sync.ps1                # normal run: download + filter
    .\bookmarks-sync.ps1 -FirstRun      # mark every file already downloaded as "seen" without
                                        # sending it to pending (skip your backlog)
    .\bookmarks-sync.ps1 -SkipDownload  # don't download, only filter

  Never touches the raw files (bookmarks\); it only reads and copies them.
#>
param(
  [switch]$FirstRun,
  [switch]$SkipDownload
)

$ErrorActionPreference = 'Stop'
$ConfigPath = if ($env:X_BOOKMARKS_CONFIG) { $env:X_BOOKMARKS_CONFIG } else { Join-Path $HOME '.x-bookmarks\config.json' }
if (-not (Test-Path $ConfigPath)) { throw "config not found: $ConfigPath (run '/x-bookmarks setup')" }
$utf8 = New-Object System.Text.UTF8Encoding($false)
$Cfg  = [IO.File]::ReadAllText($ConfigPath, $utf8) | ConvertFrom-Json

$Root    = $Cfg.tool_dir -replace '^~', $HOME
$Exe     = if ($Cfg.birdmarks_exe) { $Cfg.birdmarks_exe } else { Join-Path $Root 'birdmarks-win-x64.exe' }
$Cookie  = if ($Cfg.cookie_source) { $Cfg.cookie_source } else { 'firefox' }
$Folders = @($Cfg.x_folders | Where-Object { $_ })   # empty = take every bookmark
$Raw     = Join-Path $Root 'bookmarks'
$Pending = Join-Path $Root 'pending'
$State   = Join-Path $Root 'seen.txt'

if (-not (Test-Path $Exe)) { throw "birdmarks not found: $Exe" }
New-Item -ItemType Directory -Force $Pending | Out-Null

# Files seen before (a file is sent to pending only once)
$seen = New-Object 'System.Collections.Generic.HashSet[string]'
if (Test-Path $State) {
  foreach ($s in [IO.File]::ReadAllLines($State, $utf8)) { if ($s) { [void]$seen.Add($s) } }
}

# 1) Download only new bookmarks. With folder filtering the folder map is refreshed and folder tags are
#    written; this is the slow part (rebuilt every run).
if (-not $SkipDownload -and -not $FirstRun) {
  Write-Host '>> Downloading new bookmarks...'
  if ($Folders.Count) { & $Exe --cookie-source $Cookie --only-new --refresh-folders $Raw }
  else                { & $Exe --cookie-source $Cookie --only-new $Raw }
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "birdmarks exited with code $LASTEXITCODE (possibly a rate limit). What was downloaded is still processed; the rest comes next run."
  }
  if ($Folders.Count) {
    Write-Host '>> Updating folder tags...'
    & $Exe --backfill-folders $Raw
  }
}

# 2) Filter
$new = 0; $otherFolder = 0; $noFolder = 0
foreach ($f in (Get-ChildItem $Raw -Filter *.md -File | Sort-Object Name)) {
  if ($seen.Contains($f.Name)) { continue }

  if ($FirstRun) { [void]$seen.Add($f.Name); continue }

  $text = [IO.File]::ReadAllText($f.FullName, $utf8)
  if ($Folders.Count) {
    $m = [regex]::Match($text, '(?m)^folder:\s*"?(.*?)"?\s*$')
    if (-not $m.Success) {
      # Folder tag not written yet: do NOT mark as seen, check again next run
      $noFolder++
      continue
    }
    if ($Folders -notcontains $m.Groups[1].Value) {
      $otherFolder++
      [void]$seen.Add($f.Name)
      continue
    }
  }
  $clean = $text.Replace('&quot;', '"').Replace('&#39;', "'").Replace('&amp;', '&')
  [IO.File]::WriteAllText((Join-Path $Pending $f.Name), $clean, $utf8)
  $new++
  [void]$seen.Add($f.Name)
}

[IO.File]::WriteAllLines($State, [string[]]@($seen), $utf8)

# 3) Summary
Write-Host ''
if ($FirstRun) {
  Write-Host "First run done: $($seen.Count) existing files marked as 'seen'."
} else {
  $total = (Get-ChildItem $Pending -Filter *.md -File).Count
  Write-Host "New                : $new"
  Write-Host "Other folder       : $otherFolder (skipped)"
  Write-Host "No folder info yet : $noFolder (retried next run)"
  Write-Host "Pending total      : $total  ->  $Pending"
}
