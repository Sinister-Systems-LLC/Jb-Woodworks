# Author: RKOJ-ELENO :: 2026-05-21
# RKOJ-Setup.ps1 - First-run setup wizard for Sinister Sanctum
# Handles operator-gated items: env vars, Rust, Node.js, MCP servers, scheduled tasks,
# git config, Ollama models, and a smoke test. Each step is idempotent + skippable.
#
# Invoked via tools/session-launcher/RKOJ-Setup.bat
# Persona: EVE (Sinister Sanctum orchestration agent)

[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SanctumRoot = Split-Path -Parent $ScriptRoot
$LogPath = Join-Path $SanctumRoot '_shared-memory\PROGRESS\setup-runs.log'

# ---------- Result tracking ----------
$Script:Results = [System.Collections.ArrayList]::new()

function Add-Result {
    param(
        [string]$Step,
        [ValidateSet('done', 'skipped', 'failed', 'already-set')]
        [string]$Status,
        [string]$Detail = ''
    )
    [void]$Script:Results.Add([pscustomobject]@{
        Step    = $Step
        Status  = $Status
        Detail  = $Detail
        Time    = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssZ')
    })
}

# ---------- UI helpers ----------
function Write-Banner {
    param([string]$Text)
    $line = '=' * 70
    Write-Host ''
    Write-Host $line -ForegroundColor Magenta
    Write-Host " $Text" -ForegroundColor Magenta
    Write-Host $line -ForegroundColor Magenta
}

function Write-Step {
    param([int]$Num, [string]$Title)
    Write-Host ''
    Write-Host "[STEP $Num] $Title" -ForegroundColor Cyan
    Write-Host ('-' * 60) -ForegroundColor DarkGray
}

function Write-Skip {
    param([string]$Msg)
    Write-Host "  [SKIP] $Msg" -ForegroundColor Yellow
}

function Write-OK {
    param([string]$Msg)
    Write-Host "  [OK]   $Msg" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Msg)
    Write-Host "  [FAIL] $Msg" -ForegroundColor Red
}

function Write-Info {
    param([string]$Msg)
    Write-Host "  [INFO] $Msg" -ForegroundColor Gray
}

function Ask-YNS {
    # Returns 'Y', 'N', or 'S' (skip). Default = first letter capitalized.
    param(
        [string]$Prompt,
        [ValidateSet('Y', 'N', 'S')]
        [string]$Default = 'Y'
    )
    if ($NonInteractive) {
        Write-Info "Non-interactive mode -> defaulting to '$Default'"
        return $Default
    }
    $opts = switch ($Default) {
        'Y' { '[Y/n/s]' }
        'N' { '[y/N/s]' }
        'S' { '[y/n/S]' }
    }
    while ($true) {
        $resp = Read-Host "$Prompt $opts"
        if ([string]::IsNullOrWhiteSpace($resp)) { return $Default }
        $r = $resp.Trim().ToUpper().Substring(0, 1)
        if ($r -in @('Y', 'N', 'S')) { return $r }
        Write-Host "  Please answer Y, N, or S (skip)." -ForegroundColor Yellow
    }
}

function Read-SecretMasked {
    param([string]$Prompt)
    if ($NonInteractive) {
        Write-Info "Non-interactive mode -> skipping masked input for '$Prompt'"
        return $null
    }
    $sec = Read-Host -Prompt $Prompt -AsSecureString
    if ($null -eq $sec -or $sec.Length -eq 0) { return $null }
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try {
        return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Test-CommandExists {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    return ($null -ne $cmd)
}

function Test-EnvVarSet {
    param([string]$Name)
    $user = [Environment]::GetEnvironmentVariable($Name, 'User')
    $machine = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    return (-not [string]::IsNullOrWhiteSpace($user)) -or (-not [string]::IsNullOrWhiteSpace($machine))
}

function Set-EnvVarUser {
    param(
        [string]$Name,
        [string]$Value
    )
    if ($DryRun) {
        Write-Info "DryRun: would setx $Name (length=$($Value.Length))"
        return
    }
    # setx truncates at 1024 chars; for typical API keys this is fine.
    & setx $Name $Value | Out-Null
    [Environment]::SetEnvironmentVariable($Name, $Value, 'User')
}

# ---------- STEP 1: Env vars ----------
function Invoke-Step1-EnvVars {
    Write-Step 1 'Check environment variables (API keys + secrets)'
    $vars = @(
        @{ Name = 'ANTHROPIC_API_KEY';         Desc = 'Anthropic API key (required for Scribe/Curator/Chatbot)' }
        @{ Name = 'OPENAI_API_KEY';            Desc = 'OpenAI API key (optional - Tier-3 fallback)' }
        @{ Name = 'SINISTER_VAULT_PASSPHRASE'; Desc = 'Sinister Vault passphrase (gpg encryption)' }
    )
    foreach ($v in $vars) {
        if (Test-EnvVarSet $v.Name) {
            Write-Skip "$($v.Name) already set"
            Add-Result -Step "env:$($v.Name)" -Status 'already-set'
            continue
        }
        Write-Info $v.Desc
        $ans = Ask-YNS "Set $($v.Name) now?" 'Y'
        if ($ans -eq 'N' -or $ans -eq 'S') {
            Write-Skip "Skipping $($v.Name)"
            Add-Result -Step "env:$($v.Name)" -Status 'skipped'
            continue
        }
        $val = Read-SecretMasked "  Enter $($v.Name) (input hidden)"
        if ([string]::IsNullOrWhiteSpace($val)) {
            Write-Skip "$($v.Name) - empty input, skipping"
            Add-Result -Step "env:$($v.Name)" -Status 'skipped' -Detail 'empty-input'
            continue
        }
        try {
            Set-EnvVarUser -Name $v.Name -Value $val
            Write-OK "$($v.Name) set via setx (User scope)"
            Add-Result -Step "env:$($v.Name)" -Status 'done'
        } catch {
            Write-Fail "Failed to set $($v.Name): $_"
            Add-Result -Step "env:$($v.Name)" -Status 'failed' -Detail $_.Exception.Message
        }
    }
}

# ---------- STEP 2: Rust toolchain ----------
function Invoke-Step2-Rust {
    Write-Step 2 'Check Rust toolchain (cargo + rustc)'
    if (Test-CommandExists 'rustc') {
        $ver = & rustc --version 2>$null
        Write-OK "Rust already installed: $ver"
        Add-Result -Step 'rust' -Status 'already-set' -Detail $ver
        return
    }
    Write-Info 'Rust not detected. Required for jcode-source-level fork builds.'
    $ans = Ask-YNS 'Install Rust toolchain (~1.5 GB download)?' 'N'
    if ($ans -ne 'Y') {
        Write-Skip 'Rust install skipped - jcode-source-level fork will be unbuildable'
        Add-Result -Step 'rust' -Status 'skipped' -Detail 'jcode-fork-unbuildable'
        return
    }
    if ($DryRun) {
        Write-Info 'DryRun: would download rustup-init.exe and run silent install'
        Add-Result -Step 'rust' -Status 'skipped' -Detail 'dryrun'
        return
    }
    try {
        $tmp = Join-Path $env:TEMP 'rustup-init.exe'
        Write-Info "Downloading rustup-init.exe to $tmp ..."
        Invoke-WebRequest -Uri 'https://win.rustup.rs/x86_64' -OutFile $tmp -UseBasicParsing
        Write-Info 'Running silent install (-y default profile)...'
        & $tmp -y --default-toolchain stable --profile default | Out-Null
        Write-OK 'Rust installed. Restart shell to pick up PATH.'
        Add-Result -Step 'rust' -Status 'done' -Detail 'rustup default profile'
    } catch {
        Write-Fail "Rust install failed: $_"
        Add-Result -Step 'rust' -Status 'failed' -Detail $_.Exception.Message
    }
}

# ---------- STEP 3: Node.js ----------
function Invoke-Step3-Node {
    Write-Step 3 'Check Node.js (needed for mmdc Mermaid CLI)'
    if (Test-CommandExists 'node') {
        $ver = & node --version 2>$null
        Write-OK "Node.js already installed: $ver"
        Add-Result -Step 'node' -Status 'already-set' -Detail $ver
        return
    }
    Write-Info 'Node.js not detected.'
    $ans = Ask-YNS 'Install Node.js LTS now?' 'N'
    if ($ans -ne 'Y') {
        Write-Skip 'Node.js install skipped - mmdc-based mermaid renders will fail'
        Add-Result -Step 'node' -Status 'skipped'
        return
    }
    if ($DryRun) {
        Write-Info 'DryRun: would invoke winget/choco install'
        Add-Result -Step 'node' -Status 'skipped' -Detail 'dryrun'
        return
    }
    try {
        if (Test-CommandExists 'winget') {
            Write-Info 'Using winget...'
            & winget install --id OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements | Out-Null
            Write-OK 'Node.js LTS installed via winget'
            Add-Result -Step 'node' -Status 'done' -Detail 'winget'
        } elseif (Test-CommandExists 'choco') {
            Write-Info 'Using chocolatey...'
            & choco install nodejs-lts -y | Out-Null
            Write-OK 'Node.js LTS installed via chocolatey'
            Add-Result -Step 'node' -Status 'done' -Detail 'choco'
        } else {
            Write-Fail 'Neither winget nor choco available - manual install required (https://nodejs.org/)'
            Add-Result -Step 'node' -Status 'failed' -Detail 'no-package-manager'
        }
    } catch {
        Write-Fail "Node.js install failed: $_"
        Add-Result -Step 'node' -Status 'failed' -Detail $_.Exception.Message
    }
}

# ---------- STEP 4: MCP server install ----------
function Invoke-Step4-MCP {
    Write-Step 4 'Install MCP server fleet (Sinister Skills)'
    $installer = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\install-fleet.ps1'
    if (-not (Test-Path $installer)) {
        Write-Skip "install-fleet.ps1 not found at $installer"
        Add-Result -Step 'mcp' -Status 'skipped' -Detail 'installer-not-found'
        return
    }
    $ans = Ask-YNS 'Run MCP server fleet installer (Claude Code restart required after)?' 'Y'
    if ($ans -ne 'Y') {
        Write-Skip 'MCP fleet install skipped'
        Add-Result -Step 'mcp' -Status 'skipped'
        return
    }
    if ($DryRun) {
        Write-Info "DryRun: would invoke $installer"
        Add-Result -Step 'mcp' -Status 'skipped' -Detail 'dryrun'
        return
    }
    try {
        Write-Info "Invoking $installer ..."
        & powershell -ExecutionPolicy Bypass -File $installer
        Write-OK 'MCP fleet installer completed. RESTART Claude Code to load servers.'
        Add-Result -Step 'mcp' -Status 'done' -Detail 'restart-claude-code'
    } catch {
        Write-Fail "MCP installer failed: $_"
        Add-Result -Step 'mcp' -Status 'failed' -Detail $_.Exception.Message
    }
}

# ---------- STEP 5: Scheduled tasks ----------
function Test-TaskExists {
    param([string]$TaskName)
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    return ($null -ne $t)
}

function Invoke-Step5-ScheduledTasks {
    Write-Step 5 'Register scheduled tasks (SinisterCustodian + RKOJ auto-start)'

    # 5a - SinisterCustodian backup
    $custodianInstaller = Join-Path $SanctumRoot 'tools\sanctum-backup\install-task.ps1'
    if (Test-TaskExists 'SinisterCustodian') {
        Write-Skip 'SinisterCustodian task already registered'
        Add-Result -Step 'task:custodian' -Status 'already-set'
    } elseif (-not (Test-Path $custodianInstaller)) {
        Write-Skip "Custodian installer not found at $custodianInstaller"
        Add-Result -Step 'task:custodian' -Status 'skipped' -Detail 'installer-not-found'
    } else {
        $ans = Ask-YNS 'Register SinisterCustodian daily backup task?' 'Y'
        if ($ans -eq 'Y') {
            if ($DryRun) {
                Write-Info "DryRun: would invoke $custodianInstaller"
                Add-Result -Step 'task:custodian' -Status 'skipped' -Detail 'dryrun'
            } else {
                try {
                    & powershell -ExecutionPolicy Bypass -File $custodianInstaller
                    Write-OK 'SinisterCustodian task registered'
                    Add-Result -Step 'task:custodian' -Status 'done'
                } catch {
                    Write-Fail "Custodian task failed: $_"
                    Add-Result -Step 'task:custodian' -Status 'failed' -Detail $_.Exception.Message
                }
            }
        } else {
            Write-Skip 'Custodian task skipped'
            Add-Result -Step 'task:custodian' -Status 'skipped'
        }
    }

    # 5b - RKOJ auto-start (syncthing)
    $rkojInstaller = Join-Path $SanctumRoot 'tools\sinister-vault\syncthing\install.ps1'
    if (Test-TaskExists 'RKOJ') {
        Write-Skip 'RKOJ auto-start task already registered'
        Add-Result -Step 'task:rkoj' -Status 'already-set'
    } elseif (-not (Test-Path $rkojInstaller)) {
        Write-Skip "RKOJ installer not found at $rkojInstaller"
        Add-Result -Step 'task:rkoj' -Status 'skipped' -Detail 'installer-not-found'
    } else {
        $ans = Ask-YNS 'Register RKOJ auto-start task (Syncthing)?' 'Y'
        if ($ans -eq 'Y') {
            if ($DryRun) {
                Write-Info "DryRun: would invoke $rkojInstaller"
                Add-Result -Step 'task:rkoj' -Status 'skipped' -Detail 'dryrun'
            } else {
                try {
                    & powershell -ExecutionPolicy Bypass -File $rkojInstaller
                    Write-OK 'RKOJ task registered'
                    Add-Result -Step 'task:rkoj' -Status 'done'
                } catch {
                    Write-Fail "RKOJ task failed: $_"
                    Add-Result -Step 'task:rkoj' -Status 'failed' -Detail $_.Exception.Message
                }
            }
        } else {
            Write-Skip 'RKOJ task skipped'
            Add-Result -Step 'task:rkoj' -Status 'skipped'
        }
    }
}

# ---------- STEP 6: Git config audit ----------
function Invoke-Step6-GitAudit {
    Write-Step 6 'Audit git config (user.name + gh auth)'

    # 6a - git user.name
    $gitName = & git config --global user.name 2>$null
    if ([string]::IsNullOrWhiteSpace($gitName)) {
        Write-Info 'git user.name not set globally'
        $ans = Ask-YNS 'Set git user.name now?' 'Y'
        if ($ans -eq 'Y' -and -not $NonInteractive) {
            $name = Read-Host '  Enter git user.name'
            if (-not [string]::IsNullOrWhiteSpace($name)) {
                if (-not $DryRun) { & git config --global user.name $name | Out-Null }
                Write-OK "git user.name set to '$name'"
                Add-Result -Step 'git:user.name' -Status 'done' -Detail $name
            } else {
                Write-Skip 'Empty input, skipping'
                Add-Result -Step 'git:user.name' -Status 'skipped'
            }
        } else {
            Write-Skip 'git user.name skipped'
            Add-Result -Step 'git:user.name' -Status 'skipped'
        }
    } else {
        Write-OK "git user.name already set: $gitName"
        Add-Result -Step 'git:user.name' -Status 'already-set' -Detail $gitName
    }

    # 6b - git user.email
    $gitEmail = & git config --global user.email 2>$null
    if ([string]::IsNullOrWhiteSpace($gitEmail)) {
        Write-Info 'git user.email not set globally'
        $ans = Ask-YNS 'Set git user.email now?' 'Y'
        if ($ans -eq 'Y' -and -not $NonInteractive) {
            $email = Read-Host '  Enter git user.email'
            if (-not [string]::IsNullOrWhiteSpace($email)) {
                if (-not $DryRun) { & git config --global user.email $email | Out-Null }
                Write-OK "git user.email set to '$email'"
                Add-Result -Step 'git:user.email' -Status 'done' -Detail $email
            } else {
                Write-Skip 'Empty input, skipping'
                Add-Result -Step 'git:user.email' -Status 'skipped'
            }
        } else {
            Write-Skip 'git user.email skipped'
            Add-Result -Step 'git:user.email' -Status 'skipped'
        }
    } else {
        Write-OK "git user.email already set: $gitEmail"
        Add-Result -Step 'git:user.email' -Status 'already-set' -Detail $gitEmail
    }

    # 6c - gh auth status
    if (Test-CommandExists 'gh') {
        # Capture both streams; gh writes status to stderr typically.
        $ghOut = & gh auth status 2>&1
        $ghOk = ($LASTEXITCODE -eq 0)
        if ($ghOk) {
            Write-OK 'gh CLI authenticated'
            Add-Result -Step 'gh:auth' -Status 'already-set'
        } else {
            Write-Fail 'gh CLI NOT authenticated. Run: gh auth login'
            Add-Result -Step 'gh:auth' -Status 'failed' -Detail 'not-authenticated'
        }
    } else {
        Write-Skip 'gh CLI not installed - PR automation will be unavailable'
        Add-Result -Step 'gh:auth' -Status 'skipped' -Detail 'gh-not-installed'
    }
}

# ---------- STEP 7: Ollama models ----------
function Invoke-Step7-Ollama {
    Write-Step 7 'Pull Ollama Tier-2 LLM models'
    if (-not (Test-CommandExists 'docker')) {
        Write-Skip 'docker not installed - Ollama models skipped'
        Add-Result -Step 'ollama' -Status 'skipped' -Detail 'docker-not-installed'
        return
    }
    $dockerPs = & docker ps --filter "name=ollama" --format "{{.Names}}" 2>$null
    if ([string]::IsNullOrWhiteSpace($dockerPs)) {
        Write-Skip 'ollama container not running'
        Add-Result -Step 'ollama' -Status 'skipped' -Detail 'container-not-running'
        return
    }
    $ans = Ask-YNS 'Pull Tier-2 LLM models (qwen2.5:1.5b + qwen2.5-coder:7b + nomic-embed-text, ~5 GB)?' 'N'
    if ($ans -ne 'Y') {
        Write-Skip 'Ollama model pull skipped'
        Add-Result -Step 'ollama' -Status 'skipped'
        return
    }
    if ($DryRun) {
        Write-Info 'DryRun: would docker exec ollama ollama pull ...'
        Add-Result -Step 'ollama' -Status 'skipped' -Detail 'dryrun'
        return
    }
    $models = @('qwen2.5:1.5b', 'qwen2.5-coder:7b', 'nomic-embed-text')
    foreach ($m in $models) {
        Write-Info "Pulling $m ..."
        try {
            & docker exec ollama ollama pull $m
            if ($LASTEXITCODE -eq 0) {
                Write-OK "Pulled $m"
                Add-Result -Step "ollama:$m" -Status 'done'
            } else {
                Write-Fail "Pull failed: $m (exit $LASTEXITCODE)"
                Add-Result -Step "ollama:$m" -Status 'failed' -Detail "exit-$LASTEXITCODE"
            }
        } catch {
            Write-Fail "Pull error on $m : $_"
            Add-Result -Step "ollama:$m" -Status 'failed' -Detail $_.Exception.Message
        }
    }
}

# ---------- STEP 8: RKOJ.exe smoke test ----------
function Invoke-Step8-SmokeTest {
    Write-Step 8 'First-run smoke test (RKOJ.exe --shell /help /quit)'
    $rkojCandidates = @(
        (Join-Path $SanctumRoot 'automations\window-manager\dist\RKOJ.exe')
        (Join-Path $SanctumRoot 'automations\build\rkoj-exe\target\release\rkoj.exe')
        (Join-Path $SanctumRoot 'automations\build\forge-exe\target\release\forge.exe')
    )
    $rkojExe = $rkojCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $rkojExe) {
        Write-Skip 'RKOJ.exe not built yet - skipping smoke test'
        Add-Result -Step 'smoke' -Status 'skipped' -Detail 'rkoj-exe-not-found'
        return
    }
    $ans = Ask-YNS "Run smoke test against $rkojExe ?" 'Y'
    if ($ans -ne 'Y') {
        Write-Skip 'Smoke test skipped'
        Add-Result -Step 'smoke' -Status 'skipped'
        return
    }
    if ($DryRun) {
        Write-Info "DryRun: would invoke $rkojExe --shell with /help and /quit"
        Add-Result -Step 'smoke' -Status 'skipped' -Detail 'dryrun'
        return
    }
    try {
        # Feed /help and /quit via stdin
        $input = "/help`n/quit`n"
        $out = $input | & $rkojExe --shell 2>&1
        $joined = ($out | Out-String)
        if ($joined -match '(?i)help|command|overlay') {
            Write-OK 'Smoke test PASS - /help returned an overlay-like response'
            Add-Result -Step 'smoke' -Status 'done'
        } else {
            Write-Fail 'Smoke test inconclusive - /help did not return recognizable overlay text'
            Add-Result -Step 'smoke' -Status 'failed' -Detail 'no-overlay-match'
        }
    } catch {
        Write-Fail "Smoke test exception: $_"
        Add-Result -Step 'smoke' -Status 'failed' -Detail $_.Exception.Message
    }
}

# ---------- STEP 9: Summary + log append ----------
function Invoke-Step9-Summary {
    Write-Banner 'SUMMARY'
    $done = @($Script:Results | Where-Object { $_.Status -eq 'done' }).Count
    $already = @($Script:Results | Where-Object { $_.Status -eq 'already-set' }).Count
    $skipped = @($Script:Results | Where-Object { $_.Status -eq 'skipped' }).Count
    $failed = @($Script:Results | Where-Object { $_.Status -eq 'failed' }).Count

    Write-Host ("  Done:        {0}" -f $done)    -ForegroundColor Green
    Write-Host ("  Already-set: {0}" -f $already) -ForegroundColor DarkGreen
    Write-Host ("  Skipped:     {0}" -f $skipped) -ForegroundColor Yellow
    Write-Host ("  Failed:      {0}" -f $failed)  -ForegroundColor Red
    Write-Host ''
    Write-Host '  Per-step:' -ForegroundColor DarkGray
    foreach ($r in $Script:Results) {
        $color = switch ($r.Status) {
            'done'        { 'Green' }
            'already-set' { 'DarkGreen' }
            'skipped'     { 'Yellow' }
            'failed'      { 'Red' }
            default       { 'Gray' }
        }
        $line = "    [{0,-12}] {1}" -f $r.Status, $r.Step
        if ($r.Detail) { $line += " ($($r.Detail))" }
        Write-Host $line -ForegroundColor $color
    }

    # Append to setup-runs.log
    try {
        $logDir = Split-Path -Parent $LogPath
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        $stamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssZ')
        $header = "`n## Run @ $stamp (host=$env:COMPUTERNAME, user=$env:USERNAME, dryrun=$DryRun)`n"
        $rows = $Script:Results | ForEach-Object {
            $det = if ($_.Detail) { " ($($_.Detail))" } else { '' }
            "- [$($_.Status)] $($_.Step)$det"
        }
        $body = ($rows -join "`n") + "`n"
        $totals = "Totals: done=$done already-set=$already skipped=$skipped failed=$failed`n"
        Add-Content -Path $LogPath -Value ($header + $body + $totals) -Encoding utf8
        Write-Info "Appended summary to $LogPath"
    } catch {
        Write-Fail "Failed to append log: $_"
    }

    if ($failed -gt 0) {
        Write-Host ''
        Write-Host '  Setup completed with failures. Review summary above + log.' -ForegroundColor Red
        exit 1
    } else {
        Write-Host ''
        Write-Host '  Setup wizard complete.' -ForegroundColor Magenta
        exit 0
    }
}

# ---------- MAIN ----------
Write-Banner 'RKOJ-Setup :: Sinister Sanctum first-run wizard (EVE / RKOJ-ELENO)'
Write-Host "  SanctumRoot : $SanctumRoot"   -ForegroundColor DarkGray
Write-Host "  LogPath     : $LogPath"        -ForegroundColor DarkGray
Write-Host "  Mode        : $(if($DryRun){'DRY-RUN'}else{'LIVE'}) / $(if($NonInteractive){'NON-INTERACTIVE'}else{'INTERACTIVE'})" -ForegroundColor DarkGray

Invoke-Step1-EnvVars
Invoke-Step2-Rust
Invoke-Step3-Node
Invoke-Step4-MCP
Invoke-Step5-ScheduledTasks
Invoke-Step6-GitAudit
Invoke-Step7-Ollama
Invoke-Step8-SmokeTest
Invoke-Step9-Summary
