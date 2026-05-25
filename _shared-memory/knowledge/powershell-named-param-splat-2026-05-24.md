<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: correction
  confidence: 0.95
  reinforcements: 0
  half_life_days: 365
-->
# PowerShell named-param splat + var-shadowing gotchas

**Status:** doctrine, empirical, binding (bit sanctum lane 3 times in /loop iters 4, 5, 16)
**Created:** 2026-05-24 (iter 20 — codified after 3rd empirical hit)
**Composes with:** `powershell-out-file-bom-bites-python-readers-2026-05-23` (sibling PS gotcha doctrine)

## The two gotchas

### Gotcha 1: Array splat for named params is POSITIONAL binding

When you call a script with named params and pass them via array splat:

```powershell
# WRONG — array splat binds positionally
$ppArgs = @('-SanctumRoot', $SanctumRoot, '-Json')
& $script @ppArgs   # the `-Json` flag value goes to whatever param is next positionally

# WRONG — same trap with re-invocation pattern
$reinvokeArgs = @('-SanctumRoot', $value, '-Quick')
& $myPath @reinvokeArgs  # if script has [string]$X, [int]$Y, [switch]$Z params,
                          # value can land in the wrong param slot
```

**Correct: hashtable splat (named binding):**

```powershell
$ppParams = @{ SanctumRoot = $SanctumRoot; Json = $true }
if ($Lane) { $ppParams.Lane = $Lane }
& $script @ppParams
```

**Empirical hits:**
- **Iter 4** `per-project-protections-autofix.ps1` calling `per-project-protections-check.ps1 -Json`. Array splat → `Cannot bind argument to parameter 'InputObject' because it is null`.
- **Iter 16** `sinister-doctor.ps1` `--watch` mode re-invoking itself. Array splat → `Cannot convert value 'D:\Sinister Sanctum' to type 'System.Int32' ... 'WatchInterval'`. The `$SanctumRoot` string got routed to the `$WatchInterval` int param.

### Gotcha 2: PowerShell variable names are CASE-INSENSITIVE

When a local variable name (any case) matches a `[type]$Name` param (any case), they're the SAME variable. PowerShell coerces assignments to the param's type.

```powershell
param([switch]$Html, [string]$Lane)

# WRONG — $html shadows $Html (case-insensitive)
$html = $sb.ToString()
# -> "Cannot convert ... value of type 'System.String' to type 'System.Management.Automation.SwitchParameter'"

# WRONG — $lane shadows $Lane
foreach ($lane in $lanes) {   # each PSCustomObject gets coerced to "" (string)
    Write-Host $lane.key      # empty
}
```

**Correct: rename the local to a non-colliding identifier:**

```powershell
# Inside the param([switch]$Html) script body:
$htmlBody = $sb.ToString()    # OK

# Loop var:
foreach ($proj in $lanes) {   # $proj doesn't shadow any param
    Write-Host $proj.key      # works
}
```

**Empirical hits:**
- **Iter 5** `per-project-protections-check.ps1` `foreach ($lane in $lanes)` — `$lane` shadowed `[string]$Lane` param. Every iteration's `$lane` was an empty string instead of the PSCustomObject. Script reported "0 lanes" for 22 input lanes.
- **Iter 16** `sinister-doctor.ps1` `$html = $sb.ToString()` — same root cause. HTML report wrote 4-byte empty file.

## The unified rule

> When writing a PowerShell script with `param()` declarations:
>
> 1. **Re-invoke scripts via hashtable splat** (`@{ Name = Value; Switch = $true }`), never array splat.
> 2. **Inside the script body, NEVER reuse a param name as a local variable** (case-insensitive). Pick a different identifier.
> 3. **Always smoke-test the script with -Verbose** — silent param-binding bugs surface as either empty output or weird type-coercion errors.

## Anti-patterns

1. `& $script @($name, $value, '-flag')` — array splat passes positionally; will break when params have non-trivial types.
2. `foreach ($key in $items)` when the script has `param([string]$Key, ...)` — `$key` (case-insensitive) silently coerces collection items to strings.
3. `$html = ...` / `$json = ...` / `$lane = ...` / `$watch = ...` in any script with `[switch]$Html` / `[switch]$Json` / `[string]$Lane` / `[switch]$Watch` params — pick non-colliding identifiers.
4. Trusting `Cannot convert ... to type X` errors at face value — the actual cause is usually shadowing, not a literal type mismatch.
5. Wrapping the call in `try/catch SilentlyContinue` — these bugs SHOULD fail loud so they're caught early; silencing them masks the issue.

## Detection script (one-liner)

To find potential shadowing in any `.ps1` script:

```powershell
# Find local variable assignments that match the script's own param names
$ps = '<path>.ps1'
$params = Select-String -Path $ps -Pattern '\[[\w\[\]]+\]\$(\w+)' | ForEach-Object {
    [regex]::Match($_.Line, '\[[\w\[\]]+\]\$(\w+)').Groups[1].Value
}
foreach ($p in $params) {
    $hits = Select-String -Path $ps -Pattern "(?i)^\s*\`$$p\s*=" |
        Where-Object { $_.Line -notmatch '^\s*#' -and $_.Line -notmatch '\[(string|switch|int|bool)\]' }
    if ($hits) { Write-Host "potential shadow: \$$p in $($hits.Count) line(s)"; $hits | ForEach-Object { "  $_" } }
}
```

## Maintenance

- When this bug bites a 4th time: add empirical hit to the list above.
- When automating the detection: ship a brain-grep PreToolUse check that warns on Edit/Write of `.ps1` files containing the patterns.
- Cross-references: composes with `no-bullshit-tested-before-claimed-doctrine` (smoke-test before claim).

---

**Author:** RKOJ-ELENO :: 2026-05-24
**Lane:** sanctum-master (codified after 3 empirical hits across iters 4/5/16)
