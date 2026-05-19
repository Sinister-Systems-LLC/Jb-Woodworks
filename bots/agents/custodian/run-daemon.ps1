# Custodian daemon — calls server.py's snapshot_now in a loop
# Runs independently of Claude Code. One-shot or continuous.

[CmdletBinding()]
param(
    [switch]$OneShot,
    [int]$IntervalSeconds = 0,         # 0 = read from watch-list.json policy
    [int]$CleanupEverySeconds = 3600   # hourly cleanup pass
)

$ErrorActionPreference = 'Continue'
$AgentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = 'D:\_backups\_config\watch-list.json'
$LogDir = 'D:\_backups\_logs'
$null = New-Item -ItemType Directory -Force -Path $LogDir
$LogFile = Join-Path $LogDir ("custodian-{0:yyyyMMdd}.log" -f (Get-Date))

function Write-Log([string]$msg) {
    $line = "{0:yyyy-MM-ddTHH:mm:ssZ} {1}" -f ([DateTime]::UtcNow), $msg
    Add-Content -Path $LogFile -Value $line -Encoding utf8
    Write-Host $line
}

# Pick the agent's venv python if present, else system python
$Venv = Join-Path $AgentDir '.venv\Scripts\python.exe'
if (Test-Path $Venv) { $Python = $Venv } else { $Python = 'python' }
$ServerPy = Join-Path $AgentDir 'server.py'

if (-not (Test-Path $ServerPy)) {
    Write-Log "FATAL: server.py not found at $ServerPy"
    exit 1
}
if (-not (Test-Path $ConfigPath)) {
    Write-Log "FATAL: watch-list config not found at $ConfigPath"
    exit 1
}

# Tiny driver: import server.py, call snapshot_now / cleanup, print JSON
$DriverPy = @'
import json, sys, importlib.util, pathlib
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).parent))
spec = importlib.util.spec_from_file_location("custodian_server", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
action = sys.argv[2]
if action == "snapshot":
    print(json.dumps(mod.snapshot_now.fn() if hasattr(mod.snapshot_now, "fn") else mod.snapshot_now()))
elif action == "cleanup":
    print(json.dumps(mod.cleanup.fn() if hasattr(mod.cleanup, "fn") else mod.cleanup()))
else:
    print(json.dumps({"error": f"unknown action: {action}"}))
'@
$DriverPath = Join-Path $AgentDir '_daemon_driver.py'
Set-Content -Path $DriverPath -Value $DriverPy -Encoding utf8

function Invoke-Snapshot {
    try {
        $out = & $Python $DriverPath $ServerPy snapshot 2>&1
        $obj = $out | Select-Object -Last 1 | ConvertFrom-Json -ErrorAction Stop
        $t = $obj.totals
        Write-Log ("snapshot: new={0} unchanged={1} errors={2}" -f $t.new, $t.unchanged, $t.errors)
    } catch {
        Write-Log "snapshot ERROR: $_"
    }
}

function Invoke-Cleanup {
    try {
        $out = & $Python $DriverPath $ServerPy cleanup 2>&1
        $obj = $out | Select-Object -Last 1 | ConvertFrom-Json -ErrorAction Stop
        Write-Log ("cleanup: removed={0} kept={1} freed={2}b" -f $obj.removed, $obj.kept, $obj.freed_bytes)
    } catch {
        Write-Log "cleanup ERROR: $_"
    }
}

# Resolve interval from config policy if not set
if ($IntervalSeconds -le 0) {
    try {
        $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        $IntervalSeconds = [int]$cfg.policy.scan_interval_seconds
        if ($IntervalSeconds -le 0) { $IntervalSeconds = 120 }
    } catch {
        $IntervalSeconds = 120
    }
}

Write-Log "Custodian daemon starting (interval=${IntervalSeconds}s, cleanup=${CleanupEverySeconds}s, oneshot=$OneShot)"

if ($OneShot) {
    Invoke-Snapshot
    Invoke-Cleanup
    exit 0
}

$lastCleanup = Get-Date
while ($true) {
    Invoke-Snapshot
    if (((Get-Date) - $lastCleanup).TotalSeconds -ge $CleanupEverySeconds) {
        Invoke-Cleanup
        $lastCleanup = Get-Date
    }
    # Cheap: refresh memory-garden snapshot so bots have a fresh view
    try {
        $gardenCli = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\garden_cli.py'
        if (Test-Path $gardenCli) {
            & python $gardenCli 2>&1 | Out-Null
        }
    } catch {}
    Start-Sleep -Seconds $IntervalSeconds
}
