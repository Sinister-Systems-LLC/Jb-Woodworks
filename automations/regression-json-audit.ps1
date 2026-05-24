# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: regression-json-audit :: catch Write-Host contamination + invalid JSON
#
# Codifies iter 23's manual audit. Verifies every JSON-emitting script's stdout
# AND every generated JSON file parses cleanly via Python json.load.
#
# Origin: iter 22 caught sinister-doctor.ps1 -Json emitting non-JSON because
# sub-script Write-Host writes to the Info stream (6), not stderr (2). The fix
# was `*>&1 | Out-Null` instead of `2>&1 | Out-Null`. To prevent future
# regressions of this pattern, run this audit as part of CI / nightly cron.
#
# Exit codes:
#   0 = all surfaces parse cleanly
#   1 = at least one surface failed Python json.load
#
# Usage:
#   .\regression-json-audit.ps1                  # console summary
#   .\regression-json-audit.ps1 -Verbose         # per-surface detail
#   .\regression-json-audit.ps1 -Json            # machine-readable result

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Json
)

$auto = Join-Path $SanctumRoot 'automations'

# Surfaces to audit. Each entry: {name; type=stdout|file; cmd-or-path}
$surfaces = @(
    @{ name = 'per-project-protections-check.ps1 -Json'; type = 'stdout'; script = 'per-project-protections-check.ps1'; flags = @('-Json') }
    @{ name = 'brain-index-orphan-check.ps1 -Json';      type = 'stdout'; script = 'brain-index-orphan-check.ps1';      flags = @('-Json') }
    @{ name = 'sinister-doctor.ps1 -Quick -Json';        type = 'stdout'; script = 'sinister-doctor.ps1';               flags = @('-Quick','-Json') }
    @{ name = '_shared-memory/telemetry/_latest.json';   type = 'file';   path   = '_shared-memory\telemetry\_latest.json' }
    @{ name = '_shared-memory/inbox/_manifest.json';     type = 'file';   path   = '_shared-memory\inbox\_manifest.json' }
    @{ name = '_shared-memory/resume-search-index.json'; type = 'file';   path   = '_shared-memory\resume-search-index.json' }
)

$results = @()
$failCount = 0

# Locate python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "python not on PATH; cannot validate JSON"
    exit 2
}

foreach ($s in $surfaces) {
    $r = [ordered]@{ name = $s.name; type = $s.type; status = 'unknown'; bytes = 0; error = $null }
    try {
        if ($s.type -eq 'stdout') {
            $scriptPath = Join-Path $auto $s.script
            if (-not (Test-Path $scriptPath)) {
                $r.status = 'FAIL'
                $r.error = "script missing: $scriptPath"
                $failCount++
                $results += [PSCustomObject]$r
                continue
            }
            # Capture stdout from script as a string, write as UTF-8 no-BOM tmpfile.
            # Iter 24 fix: PowerShell's `> $tmpFile` default writes UTF-16 LE with BOM
            # which Python json.load can't read as utf-8. Use [System.IO.File]::WriteAllText
            # with UTF8Encoding($false) for compatibility (same iter 3 BOM doctrine).
            $tmpFile = [System.IO.Path]::GetTempFileName()
            $stdout = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath @($s.flags) 2>$null | Out-String
            [System.IO.File]::WriteAllText($tmpFile, $stdout, [System.Text.UTF8Encoding]::new($false))
            $r.bytes = (Get-Item $tmpFile).Length
            $parseResult = & python -c "import json, sys; json.load(open(r'$tmpFile', encoding='utf-8')); print('OK')" 2>&1
            Remove-Item $tmpFile -ErrorAction SilentlyContinue
            if ($LASTEXITCODE -eq 0 -and $parseResult -match 'OK') {
                $r.status = 'PASS'
            } else {
                $r.status = 'FAIL'
                $r.error = "$parseResult".Trim()
                $failCount++
            }
        } else {
            $filePath = Join-Path $SanctumRoot $s.path
            if (-not (Test-Path $filePath)) {
                $r.status = 'SKIP'
                $r.error = 'file not generated yet (run telemetry-rollup / inbox-manifest-build / index-resume-search to create)'
                $results += [PSCustomObject]$r
                continue
            }
            $r.bytes = (Get-Item $filePath).Length
            $parseResult = & python -c "import json; json.load(open(r'$filePath', encoding='utf-8')); print('OK')" 2>&1
            if ($LASTEXITCODE -eq 0 -and $parseResult -match 'OK') {
                $r.status = 'PASS'
            } else {
                $r.status = 'FAIL'
                $r.error = "$parseResult".Trim()
                $failCount++
            }
        }
    } catch {
        $r.status = 'FAIL'
        $r.error = $_.Exception.Message
        $failCount++
    }
    $results += [PSCustomObject]$r
}

if ($Json) {
    $out = [ordered]@{
        schema_version = 'sinister.regression-json-audit.v1'
        ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        surface_count = $results.Count
        pass_count = ($results | Where-Object { $_.status -eq 'PASS' }).Count
        fail_count = $failCount
        skip_count = ($results | Where-Object { $_.status -eq 'SKIP' }).Count
        results = $results
    }
    $out | ConvertTo-Json -Depth 5
} else {
    Write-Host ''
    Write-Host '  regression-json-audit :: ' -ForegroundColor DarkMagenta -NoNewline
    Write-Host "$($results.Count - $failCount)/$($results.Count) surfaces PASS" -ForegroundColor $(if ($failCount -eq 0) { 'Green' } else { 'Red' })
    Write-Host ''
    foreach ($r in $results) {
        $col = switch ($r.status) {
            'PASS' { 'Green' }
            'FAIL' { 'Red' }
            'SKIP' { 'Yellow' }
            default { 'DarkGray' }
        }
        $line = "  [{0,-4}] {1,-50} {2,8} bytes" -f $r.status, $r.name, $r.bytes
        if ($r.error) { $line += "  ($($r.error.Substring(0, [Math]::Min(60, $r.error.Length))))" }
        Write-Host $line -ForegroundColor $col
    }
    Write-Host ''
}

if ($failCount -gt 0) { exit 1 } else { exit 0 }
