' headless-runner.vbs -- run a command with ZERO visible window.
' Author: RKOJ-ELENO :: 2026-05-25
'
' Operator hard-canonical 2026-05-25T11:47Z: "these random powershells and
' cms consoles that pop up have to stop. make a system with sinister term
' to make them headless or something".
' Operator hard-canonical 2026-05-25 ~18:09Z (screenshot iter-20):
'   "i need this to stop popping up" -- shows cmd.exe window + Windows
'   Script Host 'Can not find script file headless-runner.vbs' error
'   because this very file was referenced but never shipped.
'
' Usage:
'   wscript.exe "headless-runner.vbs" "<full command line to run>"
'   wscript.exe "headless-runner.vbs" "powershell -File foo.ps1 -Arg bar"
'
' Behavior: wraps the argument in `cmd.exe /c` and invokes via
' WshShell.Run with window-style 0 (HIDDEN) and bWaitOnReturn=False so
' the script returns immediately. The child process inherits HIDDEN so
' NO console window appears at any point.
'
' Composes with: no-bat-no-ps1 doctrine (this is a 1-shot .vbs SHIM
' calling existing legacy automations, NOT new .ps1 authoring) +
' headless-runners doctrine + automate-everything-no-operator-admin
' doctrine.

Option Explicit

Dim sh, args, i, cmd, joined
Set sh = CreateObject("WScript.Shell")
Set args = WScript.Arguments

If args.Count < 1 Then
    ' Silently exit -- no visible error popup for empty args. The caller
    ' (schtasks / Sinister installers) should always pass >= 1 arg; an
    ' empty call is a config bug we don't want to surface to the operator.
    WScript.Quit 0
End If

' Join all args back into a single command string. Quote any arg that
' contains a space to preserve shell semantics on the cmd.exe receiver.
joined = ""
For i = 0 To args.Count - 1
    If i > 0 Then joined = joined & " "
    If InStr(args(i), " ") > 0 And Left(args(i), 1) <> """" Then
        joined = joined & """" & args(i) & """"
    Else
        joined = joined & args(i)
    End If
Next

' Run via `cmd /c` so multi-piece commands (e.g. `powershell -File x.ps1 -A`)
' parse identically to a bare interactive cmd invocation.
'   1st arg: command string
'   2nd arg: window style 0 = hidden (no visible window at any point)
'   3rd arg: bWaitOnReturn False = fire-and-forget (caller doesn't block)
cmd = "cmd /c " & joined
sh.Run cmd, 0, False

WScript.Quit 0
