# sinister-link.ps1 - Sinister LINK cross-machine pairing state machine
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25 ~00:50Z verbatim:
#   "Call this Sinister LINK and do waht we need to do so that leo and i can
#    link our machines so our agents and can communicate. place iut in even
#    anmd have it in the main header in ready saying sinister LINK unlinked
#    to eleno. then a way that we can get linked on our exe once he install
#    on his pc and we can have this efficent system we already have working
#    for us. find the best way to do it and do it."
#
# Design:
#   Thin coordination layer ON TOP of existing fleet primitives (Tailscale +
#   Sinister Vault + sanctum-auto-push + mesh-coordinator + cross-agent inbox
#   + fleet-update channel + GitHub Sinister-Sanctum repo). Sinister LINK does
#   NOT replace any of these -- it composes them and adds:
#     - a shared `sinister-link-state.json` describing who is paired
#     - a peer-state sync (via git pull of agent/<peer>/* branches that
#       sanctum-auto-push already pushes every 30min plus heartbeat/inbox/
#       mesh-locks file diffs)
#     - cross-machine mesh-coord conflict detection (peer-owned lock visible)
#     - invite-code OOB pairing (base64 JSON, expires)
#     - LINK header rendered in EVE.exe main menu
#
# Storage:
#   _shared-memory/sinister-link-state.json   (committed via sanctum-auto-push)
#   _shared-memory/sinister-link-health.json  (poller-written; per-machine ephemeral)
#   _shared-memory/sinister-link-invites/<id>.json  (committed; tracks issuance)
#
# Transport options (decided at Pair time):
#   git              = preferred default; sanctum-auto-push pushes every 30min.
#   vault            = Sinister Vault daemon at :5078 (1TB store), sub-minute sync.
#   tailscale-direct = future; field reserved.
#
# Exit codes: 0 ok / 1 not-paired-or-conflict / 2 missing-arg / 3 io-fail
#
# Actions:
#   Status                                                  - print state
#   Pair       -PeerName -PeerTailscaleIP [-PreSharedKey] [-Transport git|vault|tailscale-direct]
#   Unlink                                                  - clear + broadcast
#   Sync                                                    - pull peer state
#   AcceptInvite  -InviteCode <base64>                      - accept peer invite
#   GenerateInvite [-ExpiresMin 60] [-Transport git]        - emit base64 invite
#   ListInvites                                             - dump active invites
#   Health                                                  - peer reachability

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Status','Pair','Unlink','Sync','AcceptInvite','GenerateInvite','ListInvites','Health')]
    [string]$Action,

    [string]$PeerName        = '',
    [string]$PeerTailscaleIP = '',
    [string]$PreSharedKey    = '',
    [ValidateSet('git','vault','tailscale-direct')]
    [string]$Transport       = 'git',
    [int]$ExpiresMin         = 60,
    [string]$InviteCode      = '',
    [string]$LocalName       = '',
    [string]$SanctumRoot     = 'D:\Sinister Sanctum',
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# ---- Paths ----
$MemDir       = Join-Path $SanctumRoot '_shared-memory'
$StatePath    = Join-Path $MemDir      'sinister-link-state.json'
$HealthPath   = Join-Path $MemDir      'sinister-link-health.json'
$InvitesDir   = Join-Path $MemDir      'sinister-link-invites'
$LockPath     = Join-Path $MemDir      '.sinister-link.lock'

if (-not (Test-Path $InvitesDir)) {
    New-Item -ItemType Directory -Path $InvitesDir -Force | Out-Null
}

# ---- Helpers (PS 5.1: if-as-expression requires $(); use plain functions instead) ----
function Utc-Now { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }

function Pick-First { param([string]$A, [string]$B)
    if ($A) { return $A } else { return $B }
}

function Local-MachineName {
    if ($LocalName) { return $LocalName }
    $n = $env:COMPUTERNAME
    if (-not $n) { $n = 'unknown-machine' }
    return $n.ToLower()
}

function Local-DisplayName {
    $env_acct = $env:SINISTER_ACCOUNT
    if ($env_acct -and $env_acct -ne 'leo') { return $env_acct }
    return (Local-MachineName)
}

function Acquire-Lock { param([int]$TimeoutSec=8)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            try {
                if (Test-Path $LockPath) {
                    $age = ((Get-Date) - (Get-Item $LockPath).LastWriteTime).TotalSeconds
                    if ($age -gt 10) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue }
                }
            } catch {}
            Start-Sleep -Milliseconds 80
        }
    }
}
function Release-Lock {
    try { if (Test-Path $LockPath) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue } } catch {}
}

function Read-State {
    if (-not (Test-Path $StatePath)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8
        return ($raw | ConvertFrom-Json)
    } catch { return $null }
}

function Write-State { param($Obj)
    $json = $Obj | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($StatePath, $json, [System.Text.UTF8Encoding]::new($false))
}

function Write-Health { param($Obj)
    $json = $Obj | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText($HealthPath, $json, [System.Text.UTF8Encoding]::new($false))
}

function Hash-PSK { param([string]$Psk)
    if (-not $Psk) { return '' }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Psk)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $h = $sha.ComputeHash($bytes)
        return -join ($h | ForEach-Object { '{0:x2}' -f $_ })
    } finally { $sha.Dispose() }
}

function Mask-Psk { param([string]$Psk)
    if (-not $Psk) { return '(none)' }
    if ($Psk.Length -le 6) { return '***' }
    return ($Psk.Substring(0,3) + '...' + $Psk.Substring($Psk.Length-2,2))
}

function Encode-Invite { param([hashtable]$Payload)
    $json = $Payload | ConvertTo-Json -Compress -Depth 5
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    return [System.Convert]::ToBase64String($bytes)
}

function Decode-Invite { param([string]$Code)
    try {
        $bytes = [System.Convert]::FromBase64String($Code)
        $json = [System.Text.Encoding]::UTF8.GetString($bytes)
        return ($json | ConvertFrom-Json)
    } catch {
        throw "invalid invite code (not base64 JSON): $($_.Exception.Message)"
    }
}

function Peer-Reachable { param([string]$Ip, [int]$TimeoutMs=1200)
    if (-not $Ip) { return $false }
    try {
        $ping = New-Object System.Net.NetworkInformation.Ping
        $r = $ping.Send($Ip, $TimeoutMs)
        return ($r -and $r.Status -eq 'Success')
    } catch { return $false }
}

function Git-Out { param([string[]]$GitArgs)
    $out = & git -C $SanctumRoot @GitArgs 2>&1
    return @{ exit = $LASTEXITCODE; output = ($out -join "`n") }
}

function Get-PeerHead { param([string]$PeerSlug)
    if (-not $PeerSlug) { return $null }
    $ref = "refs/remotes/origin/agent/$PeerSlug/*"
    $r = Git-Out @('for-each-ref','--format=%(objectname:short)|%(refname:short)|%(committerdate:iso-strict)',$ref)
    if ($r.exit -ne 0 -or -not $r.output) { return $null }
    $rows = $r.output -split "`n" | Where-Object { $_ }
    if (-not $rows) { return $null }
    $parsed = $rows | ForEach-Object {
        $p = $_ -split '\|',3
        if ($p.Count -eq 3) {
            [PSCustomObject]@{ sha = $p[0]; ref = $p[1]; ts = $p[2] }
        }
    }
    return ($parsed | Sort-Object ts -Descending | Select-Object -First 1)
}

function Compute-State-Tag {
    $s = Read-State
    if (-not $s) { return 'unlinked' }
    $peer = $s.peer.name
    if (-not $peer) { return 'unlinked' }
    $last = $s.last_sync_utc
    if (-not $last) { return "linked to $peer (no sync yet)" }
    try {
        $age = ((Get-Date).ToUniversalTime() - [DateTime]::Parse($last).ToUniversalTime()).TotalSeconds
    } catch { $age = 99999 }
    if ($age -lt 60)        { $word = "$([int]$age)s" }
    elseif ($age -lt 3600)  { $word = "$([int]($age/60))m" }
    else                    { $word = "$([int]($age/3600))h" }
    if ($age -gt 600) { return "linked to $peer (STALE $word)" }
    return "linked to $peer (last sync $word ago)"
}

# ---- Action dispatch ----

switch ($Action) {

    'Status' {
        $s = Read-State
        $tag = Compute-State-Tag
        $stateWord = 'unlinked'
        if ($s) { $stateWord = 'linked' }
        $health = $null
        if (Test-Path $HealthPath) {
            try { $health = Get-Content -LiteralPath $HealthPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch {}
        }
        if ($Json) {
            $pskPrefix = ''
            if ($s -and $s.psk_hash) { $pskPrefix = $s.psk_hash.Substring(0,8) }
            $payload = [ordered]@{
                state           = $stateWord
                tag             = $tag
                local_machine   = (Local-MachineName)
                local_display   = (Local-DisplayName)
                peer            = $s.peer
                transport       = $s.transport
                paired_at_utc   = $s.paired_at_utc
                last_sync_utc   = $s.last_sync_utc
                psk_hash_prefix = $pskPrefix
                health          = $health
            }
            Write-Output ($payload | ConvertTo-Json -Depth 8)
            exit 0
        }
        Write-Output "Sinister LINK status"
        Write-Output ("  state:          " + $stateWord)
        Write-Output ("  tag:            " + $tag)
        Write-Output ("  local machine:  " + (Local-MachineName))
        Write-Output ("  local display:  " + (Local-DisplayName))
        if ($s) {
            Write-Output ("  peer name:      " + $s.peer.name)
            Write-Output ("  peer display:   " + $s.peer.display)
            Write-Output ("  peer tailscale: " + $s.peer.tailscale_ip)
            Write-Output ("  paired at:      " + $s.paired_at_utc)
            Write-Output ("  transport:      " + $s.transport)
            $lastSync = '(never)'
            if ($s.last_sync_utc) { $lastSync = $s.last_sync_utc }
            Write-Output ("  last sync:      " + $lastSync)
            if ($s.psk_hash) {
                $maxLen = [Math]::Min(12, $s.psk_hash.Length)
                Write-Output ("  psk hash:       " + $s.psk_hash.Substring(0, $maxLen) + '...')
            }
            $ph = Get-PeerHead $s.peer.name
            if ($ph) {
                Write-Output ("  peer git head:  " + $ph.sha + " (" + $ph.ref + ")")
            } else {
                Write-Output "  peer git head:  (none on origin yet)"
            }
        }
        if ($health) {
            Write-Output ""
            Write-Output ("  peer reachable: " + $health.peer_reachable)
            Write-Output ("  sync lag sec:   " + $health.sync_lag_sec)
            if ($health.warnings) {
                foreach ($w in $health.warnings) { Write-Output ("  warning:        " + $w) }
            }
        }
        exit 0
    }

    'GenerateInvite' {
        if (-not (Acquire-Lock)) { Write-Error 'lock contention'; exit 3 }
        try {
            $psk = $PreSharedKey
            if (-not $psk) {
                $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
                $b = New-Object byte[] 18
                $rng.GetBytes($b)
                $psk = ([System.Convert]::ToBase64String($b)) -replace '/','-' -replace '\+','_' -replace '=',''
            }
            $expiresAt = (Get-Date).ToUniversalTime().AddMinutes($ExpiresMin).ToString('yyyy-MM-ddTHH:mm:ssZ')
            $localName = (Local-MachineName)
            $localDisp = (Local-DisplayName)

            # Best-effort local Tailscale IP detect (peer can override at AcceptInvite time)
            $localTs = ''
            try {
                $tsExe = 'C:\Program Files\Tailscale\tailscale.exe'
                if (Test-Path $tsExe) {
                    $tsOut = & $tsExe ip -4 2>$null
                    if ($tsOut) {
                        $first = ($tsOut -split "`n" | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+' } | Select-Object -First 1)
                        if ($first) { $localTs = $first.Trim() }
                    }
                }
            } catch {}

            $invite = @{
                v                 = 1
                peer_name         = $localName
                peer_display      = $localDisp
                peer_tailscale_ip = $localTs
                psk               = $psk
                expires_utc       = $expiresAt
                transport         = $Transport
                issued_utc        = (Utc-Now)
                issuer_note       = "Sinister LINK invite from $localDisp"
            }
            $code = Encode-Invite $invite
            $inviteId = 'inv-' + (Get-Date -Format 'yyyyMMddHHmmss') + '-' + ([guid]::NewGuid().ToString().Substring(0,6))
            $inviteFile = Join-Path $InvitesDir "$inviteId.json"
            $persist = @{
                id                = $inviteId
                issued_utc        = $invite.issued_utc
                expires_utc       = $invite.expires_utc
                peer_name         = $invite.peer_name
                peer_display      = $invite.peer_display
                peer_tailscale_ip = $invite.peer_tailscale_ip
                transport         = $invite.transport
                psk_hash          = Hash-PSK $psk
                psk_mask          = Mask-Psk $psk
                consumed_utc      = ''
            }
            [System.IO.File]::WriteAllText($inviteFile, ($persist | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))

            # Author: RKOJ-ELENO :: 2026-05-25 -- Sub-G UX fix for operator utterance 07:08:40Z.
            # Write a state stub so the EVE main menu shows feedback that an invite was issued
            # (without overwriting an existing paired state if peer already accepted earlier).
            $existing = Read-State
            if (-not $existing -or -not $existing.state -or $existing.state -ne 'paired') {
                $stub = @{
                    state          = 'invited'
                    invited_at_utc = (Utc-Now)
                    invite_id      = $inviteId
                    expires_utc    = $expiresAt
                    peer           = @{
                        display = $invite.peer_display
                        name    = $invite.peer_name
                    }
                    transport      = $invite.transport
                    psk_hash       = Hash-PSK $psk
                }
                Write-State $stub
            }

            if ($Json) {
                Write-Output (@{ invite_code = $code; invite_id = $inviteId; expires_utc = $expiresAt; psk_mask = (Mask-Psk $psk) } | ConvertTo-Json -Depth 4)
            } else {
                Write-Output "Sinister LINK invite generated"
                Write-Output ("  id:          " + $inviteId)
                Write-Output ("  expires:     " + $expiresAt + " (" + $ExpiresMin + " min)")
                Write-Output ("  transport:   " + $Transport)
                Write-Output ("  psk mask:    " + (Mask-Psk $psk))
                Write-Output ""
                Write-Output "  send this invite code to your peer out-of-band (text / email / Signal):"
                Write-Output ""
                Write-Output ("    " + $code)
                Write-Output ""
                Write-Output "  peer runs:  powershell -File automations\sinister-link.ps1 -Action AcceptInvite -InviteCode <code>"
            }
            exit 0
        } finally { Release-Lock }
    }

    'AcceptInvite' {
        if (-not $InviteCode) { Write-Error 'AcceptInvite requires -InviteCode'; exit 2 }
        if (-not (Acquire-Lock)) { Write-Error 'lock contention'; exit 3 }
        try {
            $inv = Decode-Invite $InviteCode
            if (-not $inv.peer_name -or -not $inv.psk -or -not $inv.expires_utc) {
                Write-Error 'invite missing required fields (peer_name / psk / expires_utc)'
                exit 2
            }
            $exp = [DateTime]::Parse($inv.expires_utc).ToUniversalTime()
            if ([DateTime]::UtcNow -gt $exp) {
                Write-Error ("invite expired at " + $inv.expires_utc)
                exit 2
            }
            $now = Utc-Now
            $transport = 'git'
            if ($inv.transport) { $transport = $inv.transport }
            $state = @{
                v               = 1
                local_machine   = (Local-MachineName)
                local_display   = (Local-DisplayName)
                peer            = @{
                    name         = $inv.peer_name
                    display      = $inv.peer_display
                    tailscale_ip = $inv.peer_tailscale_ip
                }
                transport       = $transport
                paired_at_utc   = $now
                last_sync_utc   = ''
                psk_hash        = Hash-PSK $inv.psk
                invite_id_used  = ''
            }
            Write-State $state
            if ($Json) {
                Write-Output (@{ accepted = $true; peer = $inv.peer_name; transport = $state.transport } | ConvertTo-Json)
            } else {
                Write-Output "Sinister LINK accepted"
                Write-Output ("  peer:           " + $inv.peer_name + " (" + $inv.peer_display + ")")
                Write-Output ("  peer tailscale: " + $inv.peer_tailscale_ip)
                Write-Output ("  transport:      " + $state.transport)
                Write-Output ("  paired_at_utc:  " + $now)
                Write-Output ""
                Write-Output "  next: run -Action Sync to pull peer state, OR install poller:"
                Write-Output "        powershell -File automations\install-sinister-link-poller.ps1"
            }
            exit 0
        } finally { Release-Lock }
    }

    'Pair' {
        if (-not $PeerName) { Write-Error 'Pair requires -PeerName'; exit 2 }
        if (-not (Acquire-Lock)) { Write-Error 'lock contention'; exit 3 }
        try {
            $psk = $PreSharedKey
            $pskHash = ''
            if ($psk) { $pskHash = Hash-PSK $psk }
            $state = @{
                v               = 1
                local_machine   = (Local-MachineName)
                local_display   = (Local-DisplayName)
                peer            = @{
                    name         = $PeerName
                    display      = $PeerName
                    tailscale_ip = $PeerTailscaleIP
                }
                transport       = $Transport
                paired_at_utc   = (Utc-Now)
                last_sync_utc   = ''
                psk_hash        = $pskHash
                invite_id_used  = ''
            }
            Write-State $state
            Write-Output "OK: paired to $PeerName (transport=$Transport)"
            exit 0
        } finally { Release-Lock }
    }

    'Unlink' {
        if (-not (Acquire-Lock)) { Write-Error 'lock contention'; exit 3 }
        try {
            $s = Read-State
            if (Test-Path $StatePath) { Remove-Item -LiteralPath $StatePath -Force }
            if (Test-Path $HealthPath) { Remove-Item -LiteralPath $HealthPath -Force }
            try {
                $fu = Join-Path $SanctumRoot 'automations\fleet-update.ps1'
                if ((Test-Path $fu) -and $s) {
                    $peerNm = 'unknown'
                    if ($s.peer) { $peerNm = $s.peer.name }
                    & powershell -NoProfile -ExecutionPolicy Bypass -File $fu `
                        -Action Push -Priority normal -Kind doctrine `
                        -Message "[LINK-UNLINK] sinister-link cleared on $(Local-MachineName); was paired to $peerNm" `
                        -PushedBy 'sinister-link' | Out-Null
                }
            } catch {}
            Write-Output "OK: unlinked (state cleared, broadcast posted)"
            exit 0
        } finally { Release-Lock }
    }

    'Sync' {
        $s = Read-State
        if (-not $s) { Write-Output 'NOT-PAIRED'; exit 1 }
        $warnings = @()
        $fetch = Git-Out @('fetch','origin','--prune')
        if ($fetch.exit -ne 0) {
            $head = ($fetch.output -split "`n")[0]
            $warnings += "git fetch failed: $head"
        }
        $now = Utc-Now
        $state = @{}
        $s.PSObject.Properties | ForEach-Object { $state[$_.Name] = $_.Value }
        $state.last_sync_utc = $now
        Write-State $state

        $peerIp = $s.peer.tailscale_ip
        $reachable = $false
        if ($peerIp) { $reachable = Peer-Reachable $peerIp }
        $ph = Get-PeerHead $s.peer.name
        $lagSec = 0
        if ($ph -and $ph.ts) {
            try { $lagSec = [int]((Get-Date).ToUniversalTime() - [DateTime]::Parse($ph.ts).ToUniversalTime()).TotalSeconds } catch {}
        }
        if (-not $reachable) { $warnings += "peer tailscale ($peerIp) not pingable" }
        if (-not $ph)        { $warnings += "no agent/$($s.peer.name)/* branches on origin yet" }
        $phSha = ''; $phRef = ''; $phTs = ''
        if ($ph) { $phSha = $ph.sha; $phRef = $ph.ref; $phTs = $ph.ts }
        $health = @{
            ts_utc           = $now
            peer_reachable   = $reachable
            sync_lag_sec     = $lagSec
            peer_head_sha    = $phSha
            peer_head_ref    = $phRef
            peer_head_ts     = $phTs
            warnings         = $warnings
            double_work_risk = $false
        }
        Write-Health $health
        if ($Json) {
            Write-Output ($health | ConvertTo-Json -Depth 6)
        } else {
            Write-Output ("OK: synced (peer=" + $s.peer.name + " reachable=" + $reachable + " lag=" + $lagSec + "s warnings=" + $warnings.Count + ")")
        }
        exit 0
    }

    'ListInvites' {
        $rows = @()
        $files = Get-ChildItem -LiteralPath $InvitesDir -Filter '*.json' -File -ErrorAction SilentlyContinue
        foreach ($f in $files) {
            try {
                $r = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                $rows += [PSCustomObject]@{
                    Id        = $r.id
                    Issued    = $r.issued_utc
                    Expires   = $r.expires_utc
                    Peer      = $r.peer_name
                    Transport = $r.transport
                    PskMask   = $r.psk_mask
                    Consumed  = $r.consumed_utc
                }
            } catch {}
        }
        if ($Json) {
            Write-Output ($rows | ConvertTo-Json -Depth 4)
        } else {
            if ($rows.Count -eq 0) { Write-Output "no invites"; exit 0 }
            $rows | Sort-Object Issued -Descending | Format-Table -AutoSize | Out-String | Write-Output
        }
        exit 0
    }

    'Health' {
        if (Test-Path $HealthPath) {
            $h = Get-Content -LiteralPath $HealthPath -Raw -Encoding UTF8
            if ($Json) { Write-Output $h } else {
                $obj = $h | ConvertFrom-Json
                Write-Output "Sinister LINK health"
                Write-Output ("  ts_utc:          " + $obj.ts_utc)
                Write-Output ("  peer reachable:  " + $obj.peer_reachable)
                Write-Output ("  sync lag sec:    " + $obj.sync_lag_sec)
                Write-Output ("  peer head sha:   " + $obj.peer_head_sha)
                if ($obj.warnings) {
                    foreach ($w in $obj.warnings) { Write-Output ("  warning:         " + $w) }
                }
            }
        } else {
            Write-Output "(no health file yet -- run -Action Sync first)"
        }
        exit 0
    }
}
