# ============================================================
# hidden-spawn.ps1
# Author: RKOJ-ELENO :: 2026-05-23
# ============================================================
#
# Operator hard-canonical 2026-05-23 (verbatim):
#   "all these cmd windows that keep coming up need to be headless and
#    not seen by me. do this with out sinister term and add it as a feature"
#
# Reusable headless-spawn helper. Wrap any cmd/powershell/python invocation
# so it runs with NO visible window. Use this from hooks, scheduled tasks,
# launcher subprocesses, or anywhere a console window would otherwise flash.
#
# Three modes:
#   -PowerShellFile  <path>  -- launch a .ps1 with -WindowStyle Hidden
#   -CmdLine         <str>   -- launch an arbitrary command (cmd.exe /c) hidden
#   -PythonModule    <name>  -- launch `pythonw.exe -m <module>` (no console)
#
# Returns exit code of the wrapped process. Default -Wait so callers can
# treat it like a synchronous call; pass -NoWait for fire-and-forget.
# ============================================================

[CmdletBinding(DefaultParameterSetName='PowerShellFile')]
param(
    [Parameter(ParameterSetName='PowerShellFile', Mandatory)]
    [string]$PowerShellFile,

    [Parameter(ParameterSetName='CmdLine', Mandatory)]
    [string]$CmdLine,

    [Parameter(ParameterSetName='PythonModule', Mandatory)]
    [string]$PythonModule,

    [string[]]$Arguments = @(),
    [switch]$NoWait
)

$ErrorActionPreference = 'Continue'

switch ($PSCmdlet.ParameterSetName) {
    'PowerShellFile' {
        if (-not (Test-Path $PowerShellFile)) {
            Write-Error "hidden-spawn: file not found: $PowerShellFile"
            exit 2
        }
        $argList = @('-WindowStyle','Hidden','-NoProfile','-ExecutionPolicy','Bypass','-File',$PowerShellFile) + $Arguments
        $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -WindowStyle Hidden -PassThru
    }
    'CmdLine' {
        $argList = @('/c', $CmdLine)
        $p = Start-Process -FilePath 'cmd.exe' -ArgumentList $argList -WindowStyle Hidden -PassThru
    }
    'PythonModule' {
        # pythonw.exe is the windowless Python launcher; falls back to python.exe -W with hidden style.
        $pyw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
        if ($pyw) {
            $argList = @('-m', $PythonModule) + $Arguments
            $p = Start-Process -FilePath $pyw -ArgumentList $argList -WindowStyle Hidden -PassThru
        } else {
            $argList = @('-m', $PythonModule) + $Arguments
            $p = Start-Process -FilePath 'python.exe' -ArgumentList $argList -WindowStyle Hidden -PassThru
        }
    }
}

if ($NoWait) { exit 0 }

$p.WaitForExit()
exit $p.ExitCode
