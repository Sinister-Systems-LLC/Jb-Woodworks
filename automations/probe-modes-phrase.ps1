# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: probe Build-Phrase to verify SWARM/LOOP modes actually inject into spawn phrase.
# Smoke test: .\probe-modes-phrase.ps1
# Exits 0 = both modes detected in phrase; non-zero on fail.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$launcher = Join-Path $SanctumRoot 'automations\start-sinister-session.ps1'

# Dot-source the launcher inside a script-block so the param block doesn't execute the main flow.
# Simpler: just read Build-Phrase via regex, eval it in a stub context.

# We instead invoke launcher with a Build-Phrase-only switch we'll add temporarily — but that
# requires editing the launcher. Better: extract the function definitions and eval them here.

$lines = Get-Content $launcher -Raw

# Find Build-Phrase function block (function name -> matching closing brace at column 0)
$buildPhraseStart = $lines.IndexOf("function Build-Phrase")
if ($buildPhraseStart -lt 0) { Write-Host "[FAIL] Build-Phrase not found in launcher" -ForegroundColor Red; exit 2 }

# Use the AST to extract just Build-Phrase's body
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { Write-Host "[FAIL] parser errors in launcher" -ForegroundColor Red; exit 2 }

$funcAsts = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)
$names = @('Build-Phrase')
$funcSrc = @()
foreach ($f in $funcAsts) {
    if ($names -contains $f.Name) {
        $funcSrc += $f.Extent.Text
    }
}
if ($funcSrc.Count -eq 0) { Write-Host "[FAIL] Build-Phrase AST node not found" -ForegroundColor Red; exit 2 }

# Evaluate the function definitions into the current scope.
Invoke-Expression ($funcSrc -join "`n")

# Build a fake projRec PSCustomObject
$projRec = [pscustomobject]@{
    key = 'sanctum'
    display = 'Sinister Sanctum'
    root = 'D:\Sinister Sanctum'
    accent = 'purple'
}

# Test 1: modes off -> no SWARM/LOOP text
$modesOff = @{ swarm = $false; loop = $false }
$phraseOff = Build-Phrase $projRec 'test-modes' 'resume' $false $false $modesOff

# Test 2: swarm on
$modesS = @{ swarm = $true; loop = $false }
$phraseS = Build-Phrase $projRec 'test-modes' 'resume' $false $false $modesS

# Test 3: loop on
$modesL = @{ swarm = $false; loop = $true }
$phraseL = Build-Phrase $projRec 'test-modes' 'resume' $false $false $modesL

# Test 4: both
$modesB = @{ swarm = $true; loop = $true }
$phraseB = Build-Phrase $projRec 'test-modes' 'resume' $false $false $modesB

$pass = 0; $fail = 0
function Check([string]$name, [bool]$expected, [string]$phrase, [string]$marker) {
    $found = $phrase.Contains($marker)
    if ($found -eq $expected) {
        Write-Host "  [PASS] $name -> '$marker' $(if($expected){'present'}else{'absent'})" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "  [FAIL] $name -> '$marker' expected $(if($expected){'present'}else{'absent'}); got $(if($found){'present'}else{'absent'})" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host ''
Write-Host 'Probe: Build-Phrase modes injection' -ForegroundColor White
Write-Host '------------------------------------'
Check 'modes off : no SWARM' $false $phraseOff 'SWARM MODE on'
Check 'modes off : no LOOP'  $false $phraseOff 'LOOP MODE on'
Check 'swarm on  : SWARM in phrase' $true $phraseS 'SWARM MODE on'
Check 'swarm on  : LOOP absent'     $false $phraseS 'LOOP MODE on'
Check 'loop on   : LOOP in phrase'  $true $phraseL 'LOOP MODE on'
Check 'loop on   : SWARM absent'    $false $phraseL 'SWARM MODE on'
Check 'both on   : SWARM in phrase' $true $phraseB 'SWARM MODE on'
Check 'both on   : LOOP in phrase'  $true $phraseB 'LOOP MODE on'

Write-Host ''
Write-Host "Summary: PASS=$pass FAIL=$fail" -ForegroundColor $(if($fail -eq 0){'Green'}else{'Red'})

if ($fail -gt 0) { exit 1 } else { exit 0 }
