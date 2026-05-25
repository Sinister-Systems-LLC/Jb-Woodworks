# brain-decay-score.ps1 -- JCODE-style decay scoring for brain markdown vault
# Author: RKOJ-ELENO :: 2026-05-24
#
# Doctrine: _shared-memory/knowledge/memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24.md
# Operator hard-canonical 2026-05-24T20:36Z:
#   "make sure all our memory is concise efficent and better than jcodes"
#
# Computes per-entry effective_confidence using JCODE's formula:
#   effective_confidence = confidence × e^(-age_days / half_life × ln(2)) × sqrt(reinforcements + 1)
#
# Per-entry frontmatter convention (HTML comment block, opportunistic adoption -- only on
# entries that have it; default values applied for entries that don't):
#
#   <!-- decay:
#     category: correction | preference | fact | entity
#     confidence: 0.0-1.0
#     reinforcements: <int>
#     half_life_days: 365 | 90 | 30 | 30
#     superseded_by: <slug>  (optional; entry treated as inactive)
#   -->
#
# Default category = Fact (half-life 30d, confidence 0.8, reinforcements 0).
# Anchor date = Created or Updated field from the entry header (yyyy-mm-dd).
#
# Actions:
#   Score      [-TopDecayed N=10]     Scan + emit table sorted by lowest eff-conf first
#   Annotate   -Slug <slug> -Category fact|preference|correction|entity [-Confidence 0.8] [-Reinforcements 0]
#              Adds the frontmatter block to a specific entry (idempotent)
#   Reinforce  -Slug <slug>            Bumps reinforcements++ on the entry
#   Supersede  -Slug <slug> -By <new-slug>   Marks superseded_by
#
# Output: human-readable table (default) or -As Json for tooling.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Score','Annotate','Reinforce','Supersede','ExportIndex')] [string]$Action,

    [string]$Slug = '',
    [ValidateSet('correction','preference','fact','entity')] [string]$Category = 'fact',
    [double]$Confidence = 0.8,
    [int]$Reinforcements = 0,
    [int]$HalfLifeDays = 0,
    [string]$By = '',
    [int]$TopDecayed = 10,
    [ValidateSet('Table','Json')] [string]$As = 'Table',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$BrainDir = Join-Path $SanctumRoot '_shared-memory\knowledge'

# Half-life defaults by category (days). Matches JCODE's findings.
$HalfLifeDefault = @{
    correction = 365
    preference = 90
    fact       = 30
    entity     = 30
}

function Get-AnchorDate { param([string]$Body, [System.IO.FileInfo]$F)
    # Prefer explicit "Created: yyyy-mm-dd" in header. Fall back to filename date if present
    # (matches our -<date> slug convention). Final fallback: file mtime.
    if ($Body -match '(?im)^\*\*Created:\*\*\s*([0-9]{4}-[0-9]{2}-[0-9]{2})') {
        return [DateTime]::Parse($Matches[1])
    }
    if ($Body -match '(?im)^Created:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})') {
        return [DateTime]::Parse($Matches[1])
    }
    if ($F.BaseName -match '([0-9]{4}-[0-9]{2}-[0-9]{2})') {
        return [DateTime]::Parse($Matches[1])
    }
    return $F.LastWriteTime
}

function Parse-DecayBlock { param([string]$Body)
    # Look for <!-- decay: ... --> block. Returns hashtable or $null.
    if ($Body -notmatch '(?s)<!--\s*decay:(.*?)-->') { return $null }
    $block = $Matches[1]
    $h = @{}
    foreach ($line in ($block -split "`n")) {
        if ($line -match '^\s*([a-z_]+)\s*:\s*(.+?)\s*$') {
            $k = $Matches[1].Trim().ToLower()
            $v = $Matches[2].Trim()
            $h[$k] = $v
        }
    }
    return $h
}

function Effective-Confidence { param([double]$Conf, [int]$AgeDays, [int]$HalfLife, [int]$Reinforcements)
    if ($HalfLife -le 0) { $HalfLife = 30 }
    $decay = [Math]::Exp(-($AgeDays / $HalfLife) * [Math]::Log(2.0))
    $boost = [Math]::Sqrt([double]($Reinforcements + 1))
    return [Math]::Round($Conf * $decay * $boost, 4)
}

switch ($Action) {

    'Score' {
        $files = Get-ChildItem -LiteralPath $BrainDir -Filter '*.md' -File | Where-Object { $_.Name -ne '_INDEX.md' -and $_.Name -ne '_TEMPLATE.md' }
        $rows = @()
        $today = (Get-Date).Date
        foreach ($f in $files) {
            $body = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
            $decay = Parse-DecayBlock $body
            $cat   = if ($decay -and $decay.category)       { $decay.category }       else { 'fact' }
            $conf  = if ($decay -and $decay.confidence)     { [double]$decay.confidence } else { 0.8 }
            $reinf = if ($decay -and $decay.reinforcements) { [int]$decay.reinforcements } else { 0 }
            $half  = if ($decay -and $decay.half_life_days) { [int]$decay.half_life_days } else { $HalfLifeDefault[$cat] }
            $sup   = if ($decay -and $decay.superseded_by)  { $decay.superseded_by } else { '' }
            $anchor = Get-AnchorDate $body $f
            $ageDays = [int]($today - $anchor.Date).TotalDays
            $eff = Effective-Confidence -Conf $conf -AgeDays $ageDays -HalfLife $half -Reinforcements $reinf
            $rows += [PSCustomObject]@{
                Slug         = $f.BaseName
                Cat          = $cat
                AgeDays      = $ageDays
                HalfLife     = $half
                Conf         = $conf
                Reinf        = $reinf
                EffConf      = $eff
                Superseded   = if ($sup) { $sup } else { '' }
                Annotated    = if ($decay) { 'yes' } else { 'no (default)' }
            }
        }
        $sorted = $rows | Sort-Object EffConf  # lowest first = most decayed
        $top = $sorted | Select-Object -First $TopDecayed
        if ($As -eq 'Json') {
            $top | ConvertTo-Json -Depth 4
        } else {
            Write-Host ""
            Write-Host ("brain-decay-score :: scanned " + $rows.Count + " entries; showing TOP " + $TopDecayed + " most-decayed (lowest EffConf first)")
            Write-Host ""
            $top | Format-Table -AutoSize | Out-String | Write-Host
            $annoted = @($rows | Where-Object { $_.Annotated -eq 'yes' }).Count
            Write-Host ("  annotated: " + $annoted + " / " + $rows.Count + "  (the rest use defaults: category=fact, conf=0.8, half=30d, reinf=0)")
            Write-Host ("  ship Tier 2 by annotating more entries via: brain-decay-score.ps1 -Action Annotate -Slug <slug> -Category ...")
        }
        exit 0
    }

    'Annotate' {
        if (-not $Slug) { Write-Host "ERR: -Slug required"; exit 2 }
        $path = Join-Path $BrainDir "$Slug.md"
        if (-not (Test-Path $path)) { Write-Host "NOTFOUND: $path"; exit 1 }
        $body = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        $existing = Parse-DecayBlock $body
        $halfFinal = if ($HalfLifeDays -gt 0) { $HalfLifeDays } else { $HalfLifeDefault[$Category] }
        $newBlock = @"
<!-- decay:
  category: $Category
  confidence: $Confidence
  reinforcements: $Reinforcements
  half_life_days: $halfFinal
-->
"@
        if ($existing) {
            # Replace existing block
            $newBody = [regex]::Replace($body, '(?s)<!--\s*decay:.*?-->', $newBlock)
            $msg = "REPLACED existing decay block"
        } else {
            # Insert after first line (header). Body usually starts with "<!-- Author: ... -->"
            # Insert right after the author comment if present, else at top.
            if ($body -match '(?s)^(<!--\s*Author:.*?-->\s*\r?\n)') {
                $newBody = $body -replace [regex]::Escape($Matches[1]), ($Matches[1] + $newBlock + "`n")
                $msg = "INSERTED after Author comment"
            } else {
                $newBody = $newBlock + "`n" + $body
                $msg = "INSERTED at top"
            }
        }
        [System.IO.File]::WriteAllText($path, $newBody, [System.Text.UTF8Encoding]::new($false))
        Write-Host ("OK ({0}): {1}.md  category={2} conf={3} half={4}d reinf={5}" -f $msg, $Slug, $Category, $Confidence, $halfFinal, $Reinforcements)
        exit 0
    }

    'Reinforce' {
        if (-not $Slug) { Write-Host "ERR: -Slug required"; exit 2 }
        $path = Join-Path $BrainDir "$Slug.md"
        if (-not (Test-Path $path)) { Write-Host "NOTFOUND: $path"; exit 1 }
        $body = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        $existing = Parse-DecayBlock $body
        if (-not $existing) { Write-Host "NO-DECAY-BLOCK: annotate first via -Action Annotate"; exit 1 }
        $newReinf = [int]$existing.reinforcements + 1
        $newBody = $body -replace '(?m)(reinforcements:\s*)\d+', ('${1}' + $newReinf)
        [System.IO.File]::WriteAllText($path, $newBody, [System.Text.UTF8Encoding]::new($false))
        Write-Host ("OK: reinforced $Slug -- reinforcements " + $existing.reinforcements + " -> " + $newReinf)
        exit 0
    }

    'Supersede' {
        if (-not $Slug -or -not $By) { Write-Host "ERR: -Slug and -By required"; exit 2 }
        $path = Join-Path $BrainDir "$Slug.md"
        if (-not (Test-Path $path)) { Write-Host "NOTFOUND: $path"; exit 1 }
        $body = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        $existing = Parse-DecayBlock $body
        if (-not $existing) {
            # Insert minimal block with just superseded_by
            $minimal = "<!-- decay:`n  superseded_by: $By`n-->`n"
            if ($body -match '(?s)^(<!--\s*Author:.*?-->\s*\r?\n)') {
                $newBody = $body -replace [regex]::Escape($Matches[1]), ($Matches[1] + $minimal)
            } else {
                $newBody = $minimal + $body
            }
        } else {
            if ($existing.superseded_by) {
                $newBody = $body -replace '(?m)(superseded_by:\s*)\S+', ('${1}' + $By)
            } else {
                $newBody = $body -replace '(?s)(<!--\s*decay:[^>]*?)(-->)', ('$1  superseded_by: ' + $By + "`n$2")
            }
        }
        [System.IO.File]::WriteAllText($path, $newBody, [System.Text.UTF8Encoding]::new($false))
        Write-Host ("OK: $Slug superseded_by=$By")
        exit 0
    }

    'ExportIndex' {
        # Emit _INDEX-DECAY-SCORES.md sidecar (alphabetized; lower-risk than
        # touching every row in _INDEX.md). Cross-reference via slug column.
        $files = Get-ChildItem -LiteralPath $BrainDir -Filter '*.md' -File | Where-Object { $_.Name -ne '_INDEX.md' -and $_.Name -ne '_TEMPLATE.md' -and $_.Name -ne 'README.md' -and $_.Name -ne '_INDEX-DECAY-SCORES.md' }
        $rows = @()
        $today = (Get-Date).Date
        foreach ($f in $files) {
            $body = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
            $decay = Parse-DecayBlock $body
            $cat   = if ($decay -and $decay.category)       { $decay.category }       else { 'fact' }
            $conf  = if ($decay -and $decay.confidence)     { [double]$decay.confidence } else { 0.8 }
            $reinf = if ($decay -and $decay.reinforcements) { [int]$decay.reinforcements } else { 0 }
            $half  = if ($decay -and $decay.half_life_days) { [int]$decay.half_life_days } else { $HalfLifeDefault[$cat] }
            $sup   = if ($decay -and $decay.superseded_by)  { $decay.superseded_by } else { '' }
            $anchor = Get-AnchorDate $body $f
            $ageDays = [int]($today - $anchor.Date).TotalDays
            $eff = Effective-Confidence -Conf $conf -AgeDays $ageDays -HalfLife $half -Reinforcements $reinf
            $rows += [PSCustomObject]@{
                Slug = $f.BaseName; Cat = $cat; Age = $ageDays; Half = $half; Conf = $conf; Reinf = $reinf; EffConf = $eff; Annotated = ($decay -ne $null); Superseded = $sup
            }
        }
        $sorted = $rows | Sort-Object Slug
        $outPath = Join-Path $BrainDir '_INDEX-DECAY-SCORES.md'
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.AppendLine("<!-- Author: RKOJ-ELENO :: $(Get-Date -Format 'yyyy-MM-dd') -->")
        [void]$sb.AppendLine("<!-- AUTO-GENERATED by automations/brain-decay-score.ps1 -Action ExportIndex; do NOT hand-edit; re-run to refresh -->")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("# Sanctum brain :: decay scores (sidecar to _INDEX.md)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("**Generated:** $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')")
        [void]$sb.AppendLine("**Entries:** $($sorted.Count) total")
        [void]$sb.AppendLine("**Annotated:** $(@($sorted | Where-Object Annotated).Count) ($([math]::Round(@($sorted | Where-Object Annotated).Count / $sorted.Count * 100, 1))%)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("Formula: ``effective_confidence = confidence * exp(-(age/half_life) * ln(2)) * sqrt(reinforcements + 1)``")
        [void]$sb.AppendLine("Defaults for un-annotated: ``category=fact, confidence=0.8, half_life=30d, reinforcements=0``")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("| Slug | Cat | AgeD | HalfD | Conf | Reinf | EffConf | Annot | Superseded |")
        [void]$sb.AppendLine("|---|---|---:|---:|---:|---:|---:|---|---|")
        foreach ($r in $sorted) {
            $annot = if ($r.Annotated) { 'yes' } else { '-' }
            $sup = if ($r.Superseded) { $r.Superseded } else { '' }
            [void]$sb.AppendLine("| $($r.Slug) | $($r.Cat) | $($r.Age) | $($r.Half) | $($r.Conf) | $($r.Reinf) | $($r.EffConf) | $annot | $sup |")
        }
        [System.IO.File]::WriteAllText($outPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
        Write-Host "OK: wrote $outPath  rows=$($sorted.Count)  annotated=$(@($sorted | Where-Object Annotated).Count)"
        exit 0
    }
}
