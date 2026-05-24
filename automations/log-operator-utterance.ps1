# log-operator-utterance.ps1 — append an operator-utterance row to operator-utterances.jsonl
# Author: RKOJ-ELENO :: 2026-05-24
#
# Usage:
#   powershell -File log-operator-utterance.ps1 -SessionSlug sanctum -MessageFull "..." [-Tags "k1,k2"] [-SessionId "uuid"]
#
# Appends a JSONL line to D:\Sinister Sanctum\_shared-memory\operator-utterances.jsonl.
# Acquires lock at _shared-memory/.operator-utterances.lock; auto-extracts tags from
# the message body if -Tags omitted; sets status="new", agents_acked=[], deliverables=[].

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$SessionSlug,
    [Parameter(Mandatory=$true)] [string]$MessageFull,
    [string]$Tags = '',
    [string]$SessionId = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$TsUtc = ''
)

$ErrorActionPreference = 'Stop'
$JsonlPath = Join-Path $SanctumRoot '_shared-memory\operator-utterances.jsonl'
$LockPath  = Join-Path $SanctumRoot '_shared-memory\.operator-utterances.lock'

# Stopword list — short common words filtered from auto-tag extraction
$Stopwords = @(
    'the','and','for','with','this','that','have','from','they','them','will',
    'what','make','need','want','your','also','just','like','keep','more','only',
    'when','then','than','some','here','there','where','what','which','how','our',
    'are','was','were','has','had','its','it','to','of','in','on','at','as',
    'be','is','an','a','i','we','you','my','do','if','or','no','yes','so',
    'all','any','can','use','add','get','set','fix','run','let','out','off',
    'now','one','two','too','but','not','too','its','his','her','him','she','he'
)

function Get-AutoTags {
    param([string]$Text)
    $clean = $Text.ToLower() -replace '[^a-z0-9\s\-_]', ' '
    $words = $clean -split '\s+' | Where-Object { $_ -and $_.Length -ge 5 }
    $filtered = $words | Where-Object { $Stopwords -notcontains $_ }
    # Score by frequency
    $freq = @{}
    foreach ($w in $filtered) {
        if ($freq.ContainsKey($w)) { $freq[$w]++ } else { $freq[$w] = 1 }
    }
    $ranked = $freq.GetEnumerator() | Sort-Object -Property @{Expression='Value';Descending=$true},@{Expression='Key';Descending=$false}
    $top = @($ranked | Select-Object -First 5 | ForEach-Object { $_.Key })
    return ,$top
}

function Acquire-Lock {
    param([string]$Path, [int]$TimeoutSec = 10)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            Start-Sleep -Milliseconds 100
        }
    }
}

function Release-Lock {
    param([string]$Path)
    if (Test-Path $Path) { Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue }
}

function Get-Preview {
    param([string]$Text)
    $oneline = ($Text -replace '\s+', ' ').Trim()
    if ($oneline.Length -le 120) { return $oneline }
    return $oneline.Substring(0, 120)
}

# Resolve ts_utc
if (-not $TsUtc) { $TsUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }

# Resolve tags
if ($Tags) {
    $tagArr = @($Tags -split ',' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
} else {
    $tagArr = Get-AutoTags -Text $MessageFull
}

# Ensure JSONL file dir exists
$jsonlDir = Split-Path $JsonlPath -Parent
if (-not (Test-Path $jsonlDir)) { New-Item -ItemType Directory -Path $jsonlDir -Force | Out-Null }

# Acquire lock + append
if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) {
    Write-Error "Could not acquire lock at $LockPath after 10s"
    exit 2
}

try {
    $obj = [ordered]@{
        ts_utc          = $TsUtc
        session_slug    = $SessionSlug
        session_id      = if ($SessionId) { $SessionId } else { $null }
        preview         = Get-Preview -Text $MessageFull
        tags            = @($tagArr)
        status          = 'new'
        agents_acked    = @()
        deliverables    = @()
        resolved_at_utc = $null
        message_full    = $MessageFull
    }
    $json = $obj | ConvertTo-Json -Compress -Depth 10
    # Append with explicit UTF-8 (no BOM) — one line per row
    $sw = [System.IO.StreamWriter]::new($JsonlPath, $true, [System.Text.UTF8Encoding]::new($false))
    $sw.WriteLine($json)
    $sw.Close()
    Write-Output $TsUtc
} finally {
    Release-Lock -Path $LockPath
}
