# agent-dispatch.ps1 -- run a sanctum-automation tool on an already-open agent
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T21:32Z (verbatim):
#   "add support to run a selected tool on already open agents"
#
# Mechanism: inbox-based dispatch. Operator (via EVE.exe automation menu OR
# direct CLI) writes a tool-dispatch message into _shared-memory/inbox/<target-slug>/.
# The target agent's standard inbox-poll picks it up on its next turn, runs the
# tool with provided args, and writes a result row back into requester's inbox.
#
# Tool whitelist (allow-list — agents must NOT run arbitrary scripts):
#   - brain-decay-score    (Score|Annotate|Reinforce|Supersede)
#   - heartbeat-sweep      (default dry-run)
#   - mesh-coordinator     (Sweep|List)
#   - bot-lifecycle        (List|Sweep|Status)
#   - link-ingest          (List|Status)
#   - link-route           (Status|RouteAll)
#   - contradict           (Audit|Tally|Walk)
#   - claude-accounts-status (Board|Bar|Json)
#   - fleet-update         (List|Stats)
#   - fleet-autostart      (Status)
#
# Actions:
#   Dispatch  -Target <slug> -Tool <tool> [-Args "..."]   write dispatch msg
#   Inbox     -Slug <slug>                                list pending tool-dispatch msgs for this slug
#   Run       -MessageFile <path>                          (called by receiving agent) execute the tool
#   Result    -Target <slug> -DispatchId <id> -Result <txt>  (called by receiving agent) post result back
#   List      [-Hours 1]                                   recent dispatch traffic across fleet
#
# Composes with: mesh-coordinator.ps1 (target picks up its own focus before running);
# sinister-bus inbox doctrine (canonical fleet message bus); CLAUDE.md cold-start
# step 11 (sibling-detect + fleet-update poll + mesh-coord Check).

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [ValidateSet('Dispatch','Inbox','Run','Result','List')] [string]$Action,
    [string]$Target = '',
    [string]$Slug = '',
    [string]$Tool = '',
    [string]$Args = '',
    [string]$MessageFile = '',
    [string]$DispatchId = '',
    [string]$Result = '',
    [int]$Hours = 1,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$InboxRoot = Join-Path $SanctumRoot '_shared-memory\inbox'

# Tool allow-list -- script_name + default safe args
$TOOL_REGISTRY = @{
    'brain-decay-score'      = @{ script='brain-decay-score.ps1';      default_args=@('-Action','Score','-TopDecayed','10') }
    'heartbeat-sweep'        = @{ script='heartbeat-sweep.ps1';        default_args=@('-MaxAgeHours','24') }
    'mesh-coordinator'       = @{ script='mesh-coordinator.ps1';       default_args=@('-Action','List') }
    'bot-lifecycle'          = @{ script='bot-lifecycle.ps1';          default_args=@('-Action','List') }
    'link-ingest'            = @{ script='link-ingest.ps1';            default_args=@('-Action','Status') }
    'link-route'             = @{ script='link-route.ps1';             default_args=@('-Action','Status') }
    'contradict'             = @{ script='contradict.ps1';             default_args=@('-Action','Audit','-WindowDays','7') }
    'claude-accounts-status' = @{ script='claude-accounts-status.ps1'; default_args=@('-Mode','Board') }
    'fleet-update'           = @{ script='fleet-update.ps1';           default_args=@('-Action','Stats') }
    'fleet-autostart'        = @{ script='fleet-autostart.ps1';        default_args=@('-Mode','Status') }
}

function Utc-Now { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function New-Id  { return ([guid]::NewGuid().ToString('N').Substring(0,10)) }

switch ($Action) {

    'Dispatch' {
        if (-not $Target -or -not $Tool) { Write-Host "ERR: -Target and -Tool required"; exit 2 }
        if (-not $TOOL_REGISTRY.ContainsKey($Tool)) {
            Write-Host ("ERR: tool '$Tool' not in allow-list. Allowed: " + (($TOOL_REGISTRY.Keys | Sort-Object) -join ', '))
            exit 2
        }
        $targetDir = Join-Path $InboxRoot $Target
        if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
        $dispatchId = New-Id
        $ts = Utc-Now
        $tsFile = ((Utc-Now) -replace ':','' -replace '-','')
        # Args: comma-sep override OR registry default
        $resolvedArgs = if ($Args) { @($Args -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) } else { $TOOL_REGISTRY[$Tool].default_args }
        $msg = [pscustomobject]@{
            _author      = 'RKOJ-ELENO :: 2026-05-24'
            tag          = '[TOOL-DISPATCH]'
            from         = 'sanctum'
            to           = $Target
            ts_utc       = $ts
            dispatch_id  = $dispatchId
            tool         = $Tool
            script       = $TOOL_REGISTRY[$Tool].script
            args         = $resolvedArgs
            subject      = "Run sanctum tool '$Tool' and post result back via agent-dispatch.ps1 -Action Result"
            instructions = "Read agent-dispatch.ps1 -Action Run -MessageFile <this-file-path> to execute, then post result via agent-dispatch.ps1 -Action Result -Target sanctum -DispatchId $dispatchId -Result <output>"
            status       = 'pending'
        }
        $outPath = Join-Path $targetDir "$tsFile-tool-dispatch-$dispatchId.json"
        $json = $msg | ConvertTo-Json -Depth 6
        [System.IO.File]::WriteAllText($outPath, $json, [System.Text.UTF8Encoding]::new($false))
        Write-Host ("OK: dispatched tool=$Tool to target=$Target  id=$dispatchId")
        Write-Host ("  message: $outPath")
        Write-Host ("  target's next inbox-poll will surface this")
        exit 0
    }

    'Inbox' {
        if (-not $Slug) { Write-Host "ERR: -Slug required"; exit 2 }
        $dir = Join-Path $InboxRoot $Slug
        if (-not (Test-Path $dir)) { Write-Host "no inbox dir for slug=$Slug"; exit 0 }
        $msgs = @(Get-ChildItem -LiteralPath $dir -Filter '*-tool-dispatch-*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name)
        if ($msgs.Count -eq 0) { Write-Host "no tool-dispatch messages for $Slug"; exit 0 }
        Write-Host ("tool-dispatch messages for $Slug : $($msgs.Count)")
        foreach ($m in $msgs) {
            try {
                $obj = Get-Content -LiteralPath $m.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                Write-Host ("  $($obj.ts_utc)  tool=$($obj.tool)  id=$($obj.dispatch_id)  status=$($obj.status)  from=$($obj.from)")
            } catch {
                Write-Host ("  [unreadable] $($m.Name)")
            }
        }
        exit 0
    }

    'Run' {
        if (-not $MessageFile) { Write-Host "ERR: -MessageFile required"; exit 2 }
        if (-not (Test-Path $MessageFile)) { Write-Host "NOTFOUND: $MessageFile"; exit 1 }
        $msg = Get-Content -LiteralPath $MessageFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($msg.tag -ne '[TOOL-DISPATCH]') { Write-Host "ERR: not a tool-dispatch message"; exit 1 }
        $toolName = $msg.tool
        if (-not $TOOL_REGISTRY.ContainsKey($toolName)) { Write-Host "ERR: tool '$toolName' not in allow-list"; exit 1 }
        $scriptPath = Join-Path $SanctumRoot ('automations\' + $TOOL_REGISTRY[$toolName].script)
        if (-not (Test-Path $scriptPath)) { Write-Host "ERR: script $scriptPath missing"; exit 1 }
        $argList = if ($msg.args) { @($msg.args) } else { $TOOL_REGISTRY[$toolName].default_args }
        Write-Host ("EXEC tool=$toolName script=$($TOOL_REGISTRY[$toolName].script) args=" + ($argList -join ' '))
        $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath @argList 2>&1 | Out-String
        Write-Host $out
        Write-Host ("--- exit=$LASTEXITCODE ---")
        # Post result back automatically
        if ($msg.from) {
            $resultArgs = @('-Action','Result','-Target',$msg.from,'-DispatchId',$msg.dispatch_id,'-Result',("exit=$LASTEXITCODE`n" + $out.Substring(0, [Math]::Min(4000, $out.Length))))
            $self = $PSCommandPath
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $self @resultArgs 2>&1 | Out-Null
        }
        # Mark message handled
        $msg | Add-Member -MemberType NoteProperty -Name 'status' -Value 'handled' -Force
        $msg | Add-Member -MemberType NoteProperty -Name 'handled_at_utc' -Value (Utc-Now) -Force
        [System.IO.File]::WriteAllText($MessageFile, ($msg | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))
        exit 0
    }

    'Result' {
        if (-not $Target -or -not $DispatchId) { Write-Host "ERR: -Target and -DispatchId required"; exit 2 }
        $targetDir = Join-Path $InboxRoot $Target
        if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
        $tsFile = ((Utc-Now) -replace ':','' -replace '-','')
        $resMsg = [pscustomobject]@{
            _author     = 'RKOJ-ELENO :: 2026-05-24'
            tag         = '[TOOL-RESULT]'
            from        = 'agent-dispatch'
            to          = $Target
            ts_utc      = Utc-Now
            dispatch_id = $DispatchId
            result      = $Result
            status      = 'new'
        }
        $out = Join-Path $targetDir "$tsFile-tool-result-$DispatchId.json"
        [System.IO.File]::WriteAllText($out, ($resMsg | ConvertTo-Json -Depth 4), [System.Text.UTF8Encoding]::new($false))
        Write-Host ("OK: result posted to $Target id=$DispatchId")
        exit 0
    }

    'List' {
        $cutoff = (Get-Date).ToUniversalTime().AddHours(-$Hours)
        $rows = @()
        foreach ($d in Get-ChildItem -LiteralPath $InboxRoot -Directory -ErrorAction SilentlyContinue) {
            foreach ($f in Get-ChildItem -LiteralPath $d.FullName -Filter '*-tool-dispatch-*.json' -File -ErrorAction SilentlyContinue) {
                try {
                    $obj = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                    $ts = [DateTime]::Parse($obj.ts_utc).ToUniversalTime()
                    if ($ts -gt $cutoff) {
                        $rows += [PSCustomObject]@{
                            Ts = $obj.ts_utc; From = $obj.from; To = $d.Name; Tool = $obj.tool; Status = $obj.status
                        }
                    }
                } catch {}
            }
        }
        if ($rows.Count -eq 0) { Write-Host "no dispatch traffic in last ${Hours}h"; exit 0 }
        $rows | Sort-Object Ts -Descending | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }
}
