# Author: RKOJ-ELENO :: 2026-05-25
#
# brain-auto-annotate.ps1 -- defensive sweep that keeps the brain at 100%
# annotation even when sibling lanes add new entries faster than the master
# can hand-annotate.
#
# Operator hard-canonical 2026-05-25T~02:50Z verbatim:
#     "keep pushing to 100 percent. then make all tools and then keep
#      expanding memory and make sure ALL agents have the memory updates."
#
# Composes with:
#   - brain-decay-implementation-schema-2026-05-25 (the decay frontmatter contract)
#   - memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24 (Tier 2 scoring)
#   - gradual-growth-memory-push-eve-exe-ready-2026-05-24 (R3 prune-as-add)
#   - no-bullshit-tested-before-claimed-doctrine-2026-05-23 (rule 5 forever-upgrade)
#
# What it does:
#   For every *.md in _shared-memory/knowledge/ (excluding _INDEX, _TEMPLATE,
#   _INDEX-DECAY-SCORES, README) that LACKS a `decay:` HTML comment block in
#   the first 10 lines, infer sensible defaults from the filename + content
#   and inject the frontmatter via brain-decay-score.ps1 -Action Annotate.
#
# Defaults heuristic (filename-substring -> (category, confidence, half_life)):
#   doctrine|canonical|directive|policy|playbook -> preference / 1.0 / 365
#   audit|findings|investigation|smoke|verified  -> fact       / 0.9  / 180
#   bug|fix|regression|fail|crash               -> correction / 1.0  / 365
#   issue|lesson|gotcha|trap                    -> correction / 0.95 / 365
#   pattern|architecture|design|spec            -> fact       / 0.85 / 180
#   *                                            -> fact       / 0.85 / 180  (safe default)
#
# Usage:
#   powershell -NoProfile -File automations\brain-auto-annotate.ps1
#   powershell -NoProfile -File automations\brain-auto-annotate.ps1 -DryRun
#
# Exit codes:
#   0 = OK (zero or more entries annotated; no errors)
#   1 = at least one annotation failed (continued past it; rest still tried)
#   2 = sanctum root / brain dir missing

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$brainDir = Join-Path $SanctumRoot '_shared-memory\knowledge'
$scoreScript = Join-Path $SanctumRoot 'automations\brain-decay-score.ps1'

if (-not (Test-Path $brainDir)) {
    Write-Host "brain-dir missing: $brainDir"; exit 2
}
if (-not (Test-Path $scoreScript)) {
    Write-Host "brain-decay-score.ps1 missing: $scoreScript"; exit 2
}

$skip = @('_INDEX.md','_INDEX-DECAY-SCORES.md','README.md','_TEMPLATE.md')

function Infer-Defaults {
    param([string]$Slug)
    $lower = $Slug.ToLower()
    if     ($lower -match 'doctrine|canonical|directive|policy|playbook|charter') {
        return @('preference', 1.0, 365)
    }
    elseif ($lower -match 'bug|fix|regression|fail|crash|broken') {
        return @('correction', 1.0, 365)
    }
    elseif ($lower -match 'issue|lesson|gotcha|trap|antipattern') {
        return @('correction', 0.95, 365)
    }
    elseif ($lower -match 'audit|findings|investigation|smoke|verified|probe') {
        return @('fact', 0.9, 180)
    }
    elseif ($lower -match 'pattern|architecture|design|spec|schema') {
        return @('fact', 0.85, 180)
    }
    else {
        return @('fact', 0.85, 180)
    }
}

$found = 0
$annotated = 0
$failed = 0

Get-ChildItem -LiteralPath $brainDir -Filter '*.md' | ForEach-Object {
    if ($skip -contains $_.Name) { return }
    $head = (Get-Content -LiteralPath $_.FullName -TotalCount 12 -ErrorAction SilentlyContinue) -join "`n"
    if ($head -match 'decay:') { return }
    $found++
    $slug = $_.BaseName  # filename without .md extension
    $defaults = Infer-Defaults $slug
    $cat = $defaults[0]; $conf = $defaults[1]; $half = $defaults[2]
    if (-not $Quiet) {
        Write-Host ("[unannotated] {0} -> ({1}/{2}/{3}d){4}" -f $slug, $cat, $conf, $half, ($(if($DryRun){' [DRY]'}else{''})))
    }
    if (-not $DryRun) {
        $r = & $scoreScript -Action Annotate -Slug $slug -Category $cat -Confidence $conf -HalfLifeDays $half 2>&1 | Out-String
        if ($r -match '^OK') {
            $annotated++
        } else {
            $failed++
            Write-Host "  FAIL: $($r -split "`n" | Select-Object -First 1)"
        }
    }
}

if (-not $Quiet) {
    Write-Host ("brain-auto-annotate :: found={0} annotated={1} failed={2}" -f $found, $annotated, $failed)
}
if ($failed -gt 0) { exit 1 } else { exit 0 }
