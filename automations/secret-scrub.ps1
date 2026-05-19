# secret-scrub.ps1 - scan Sinister LLC for committed secrets BEFORE git operations.
# Operator-run. Outside Claude's sandbox so it can read everything.
# Emits a runlog manifest.

[CmdletBinding()]
param(
    [string]$LLCRoot = 'D:\Sinister Sanctum',
    [string]$Path = '',                          # optional: scan only this subpath
    [switch]$DryRun,                             # report, do not modify
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

# Load runlog helper from the canonical hub (LLC mirrors it later)
$RunlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $RunlogHelper) { . $RunlogHelper }
if (Get-Command Start-Runlog -ErrorAction SilentlyContinue) {
    $log = Start-Runlog -Script 'secret-scrub'
}

$scanRoot = if ($Path) { Join-Path $LLCRoot $Path } else { $LLCRoot }

if (-not (Test-Path $scanRoot)) {
    Write-Host "FAIL: scan root not found: $scanRoot" -ForegroundColor Red
    exit 1
}

# Patterns and their labels. Tuned for FALSE-POSITIVE-AVERSE.
$Patterns = @(
    @{ rx = 'sk-ant-[a-zA-Z0-9_-]{30,}';     label = 'Anthropic API key' }
    @{ rx = 'sk-[a-zA-Z0-9_-]{40,}';         label = 'OpenAI API key' }
    @{ rx = 'AIza[a-zA-Z0-9_-]{30,}';        label = 'Google API key' }
    @{ rx = 'ghp_[a-zA-Z0-9]{30,}';          label = 'GitHub PAT (classic)' }
    @{ rx = 'gho_[a-zA-Z0-9]{30,}';          label = 'GitHub OAuth' }
    @{ rx = 'github_pat_[a-zA-Z0-9_]{60,}';  label = 'GitHub PAT (fine-grained)' }
    @{ rx = 'xox[bpsoa]-[a-zA-Z0-9-]{10,}';  label = 'Slack token' }
    @{ rx = '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'; label = 'PEM private key' }
)

# File-name patterns that are themselves a smell
$DangerFiles = @(
    '\.env$',
    'credentials\.json$',
    '\.pem$', '\.p12$', '\.pfx$', '\.cer$', '\.crt$',
    'id_rsa$', 'id_ed25519$',
    'yurikey.*\.xml$',
    'keybox.*\.xml$'
)

$hits = @()
$dangerFileHits = @()
$filesScanned = 0
$filesSkipped = 0

Write-Host "Scanning $scanRoot (DryRun=$DryRun)..." -ForegroundColor Cyan

# Get-ChildItem walk with explicit exclusions
$excludeDirs = @('node_modules', '.venv', '__pycache__', '.git', 'build', 'dist', '_backups', '_logs', 'runtime-state')
Get-ChildItem -Path $scanRoot -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    $relPath = $_.FullName.Replace($scanRoot + '\', '')
    foreach ($d in $excludeDirs) {
        if ($_.FullName -like "*\$d\*") { $filesSkipped++; return }
    }
    if ($_.Length -gt 5242880) { $filesSkipped++; return }   # skip files > 5MB

    # Danger-file name check
    foreach ($df in $DangerFiles) {
        if ($_.Name -match $df) {
            $dangerFileHits += [pscustomobject]@{ path = $relPath; pattern = "filename:$df" }
            break
        }
    }

    # Content scan (text files only)
    if ($_.Extension -in @('.md', '.txt', '.json', '.yaml', '.yml', '.py', '.ps1', '.bat', '.js', '.ts', '.kt', '.java', '.sh', '.env', '.conf', '.ini')) {
        $filesScanned++
        try {
            $content = Get-Content -Path $_.FullName -Raw -Encoding utf8 -ErrorAction Stop
        } catch { return }
        if ([string]::IsNullOrEmpty($content)) { return }
        foreach ($p in $Patterns) {
            $m = [regex]::Matches($content, $p.rx)
            if ($m.Count -gt 0) {
                # Don't print the matched value; only the path + label
                $hits += [pscustomobject]@{ path = $relPath; pattern = $p.label; count = $m.Count }
            }
        }
    }
}

Write-Host ""
Write-Host "=== RESULTS ===" -ForegroundColor Cyan
Write-Host "Files scanned: $filesScanned (skipped $filesSkipped excluded/large)"
Write-Host ""

if ($dangerFileHits.Count -gt 0) {
    Write-Host "DANGER FILES (by name):" -ForegroundColor Red
    $dangerFileHits | Format-Table -AutoSize | Out-String | Write-Host
}
if ($hits.Count -gt 0) {
    Write-Host "SECRET PATTERNS (by content):" -ForegroundColor Red
    $hits | Sort-Object path | Format-Table -AutoSize | Out-String | Write-Host
}
if ($dangerFileHits.Count -eq 0 -and $hits.Count -eq 0) {
    Write-Host "  [OK] No secrets detected." -ForegroundColor Green
}

# Runlog
if ($log) {
    Add-RunlogStep -Log $log -Name 'scrub-scan' -Ok ($hits.Count -eq 0 -and $dangerFileHits.Count -eq 0) `
        -Summary "$filesScanned files; $($hits.Count) content hits; $($dangerFileHits.Count) danger files" `
        -Errors (@($hits + $dangerFileHits) | ForEach-Object { "$($_.pattern) in $($_.path)" })
    Set-RunlogOutput -Log $log -Key 'files_scanned' -Value $filesScanned
    Set-RunlogOutput -Log $log -Key 'content_hits' -Value $hits.Count
    Set-RunlogOutput -Log $log -Key 'danger_files' -Value $dangerFileHits.Count
    if ($hits.Count -gt 0 -or $dangerFileHits.Count -gt 0) {
        Add-RunlogNextAction -Log $log -Action 'Operator: remove or .gitignore the listed paths before pushing this repo.'
    }
    $manifestPath = Save-Runlog -Log $log -AutoClose:(-not ($hits.Count -gt 0))
    Write-Host ""
    Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray
}

if ($hits.Count -gt 0 -or $dangerFileHits.Count -gt 0) {
    Write-Host ""
    Write-Host "ACTION: remove or .gitignore the listed paths before pushing." -ForegroundColor Yellow
    if (-not $Quiet) { Read-Host 'Press Enter to close' }
    exit 1
}

exit 0
