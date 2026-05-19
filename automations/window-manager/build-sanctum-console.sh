#!/usr/bin/env bash
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# build-sanctum-console.sh — one-click rebuild of RKOJ.exe.
# (Filename retained for back-compat with operator's Build-Sanctum-Console.bat
#  Desktop entry; output binary is RKOJ.exe in dist/RKOJ/.)
#
# 10-step pipeline. Warm path (env intact, hooks present): <30 s.
# Cold path (no venv): <90 s. Failure surfaces within ~5 s of trigger.
#
# Why bash, not PowerShell:
#   git-bash cold start ~80 ms vs PowerShell 5.1 ~1.5 s; saves ~14 s over
#   the 10-step pipeline. Plus: forward slashes, cygpath, real &&/||, no
#   em-dash parser quirks, `time` per phase for honest budgeting.
#
# Gotchas baked in (see BUILD.md cross-links):
#   - Never `pip install --upgrade pip` in a fresh venv  (pip-self-upgrade-breaks-venv)
#   - Force-reinstall pyinstaller-hooks-contrib on cold  (pyinstaller-tomli-hook-missing)
#   - Robocopy /MIR (not cp -ru) for the Desktop sync    (exe-dll-crash-incomplete-copy)
#
# Operator entry: C:\Users\Zonia\Desktop\Build-Sanctum-Console.bat
# Direct manual: bash "D:/Sinister Sanctum/automations/window-manager/build-sanctum-console.sh"

set -euo pipefail
# `set -o pipefail` ensures `python | tee` propagates pyinstaller's exit code
# rather than tee's (always 0). Without it, build failures look like successes.
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_build-helpers.sh"

cd "$SCRIPT_DIR"

# Shared paths (POSIX inside git-bash; convert with cygpath_w for native tools).
SANCTUM_ROOT="/d/Sinister Sanctum"
SHARED_MEM="$SANCTUM_ROOT/_shared-memory"
HEARTBEAT_DIR="$SHARED_MEM/heartbeats"
PROGRESS_FILE="$SHARED_MEM/PROGRESS/Sinister Sanctum.md"
RUNLOG_DIR="/d/Sinister/Sinister Skills/12_LLM_ORCHESTRATION/runtime-state/script-runs"
BUILD_LOG_DIR="$SCRIPT_DIR/_build-logs"
DESKTOP_DIR_UNIX="$(cygpath -u "${USERPROFILE:-C:/Users/$USER}")/Desktop/RKOJ"

START_ISO="$(utc_iso)"
START_STAMP="$(utc_stamp)"
mkdir -p "$BUILD_LOG_DIR"
mkdir -p "$HEARTBEAT_DIR"
BUILD_LOG="$BUILD_LOG_DIR/build-$START_STAMP.log"

# Step result accumulator for the runlog manifest at step 10.
# Format per line: "<n>|<name>|<ok 0/1>|<ms>|<summary>"
STEP_LOG="$(mktemp -t sanctum-build-steps-XXXXXX)"
trap 'rm -f "$STEP_LOG"' EXIT

record_step() {
    local n="$1" name="$2" okflag="$3" ms="$4"
    local summary="${5:-}"
    printf '%s|%s|%s|%s|%s\n' "$n" "$name" "$okflag" "$ms" "$summary" >> "$STEP_LOG"
}

# Pretty banner.
printf '\n  %s================================================================%s\n' "$_C_MAGENTA" "$_C_RESET"
printf '   %sB U I L D   R K O J . E X E%s\n' "$_C_BOLD" "$_C_RESET"
printf '   %sone-click rebuild | pyinstaller onedir | robocopy mirror%s\n' "$_C_DIM" "$_C_RESET"
printf '  %s================================================================%s\n' "$_C_MAGENTA" "$_C_RESET"

# ---------------------------------------------------------------------------
# [1] Banner + cd + fail-fast on missing src
step 1 "Verify source tree"
t0
[[ -f "$SCRIPT_DIR/desktop_app.py"   ]] || die "desktop_app.py not found"
[[ -f "$SCRIPT_DIR/server.py"        ]] || die "server.py not found"
[[ -f "$SCRIPT_DIR/RKOJ.spec"        ]] || die "RKOJ.spec not found"
[[ -f "$SCRIPT_DIR/requirements.txt" ]] || die "requirements.txt not found"
ok "spec + sources present"
S1_MS="$(t1)"
record_step 1 verify-src 1 "${S1_MS%ms}" "all 4 source files present"

# ---------------------------------------------------------------------------
# [2] Resolve Python interpreter
step 2 "Resolve Python interpreter"
t0
PYTHON=""
if [[ -x "$SCRIPT_DIR/.venv/Scripts/python.exe" ]]; then
    PYTHON="$SCRIPT_DIR/.venv/Scripts/python.exe"
elif command -v py >/dev/null 2>&1; then
    if py -3.12 -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
        PYTHON="py -3.12"
    fi
fi
if [[ -z "$PYTHON" ]] && command -v python >/dev/null 2>&1; then
    PYTHON="python"
fi
if [[ -z "$PYTHON" ]]; then
    die "no usable python on PATH (.venv missing AND no py/python)"
fi
PYTHON_VER="$("$PYTHON" --version 2>&1 || echo unknown)"
ok "using: $PYTHON ($PYTHON_VER)"
S2_MS="$(t1)"
record_step 2 resolve-python 1 "${S2_MS%ms}" "$PYTHON_VER"

# ---------------------------------------------------------------------------
# [3] Warm-path probe — skip 4..6 if everything already in place
step 3 "Warm-path probe"
t0
WARM=0
HOOK_FILE="$SCRIPT_DIR/.venv/Lib/site-packages/PyInstaller/hooks/pre_safe_import_module/hook-tomli.py"
if "$PYTHON" -c "import fastapi, uvicorn, webview, qrcode, PyInstaller, PyInstaller.hooks.pre_safe_import_module" >/dev/null 2>&1; then
    if [[ -f "$HOOK_FILE" ]]; then
        WARM=1
    fi
fi
if (( WARM )); then
    ok "WARM — env + tomli hook present, skipping steps 4-6"
    S3_MS="$(t1)"
    record_step 3 warm-probe 1 "${S3_MS%ms}" "warm"
else
    warn "COLD — will run venv/req/hooks-contrib steps"
    S3_MS="$(t1)"
    record_step 3 warm-probe 1 "${S3_MS%ms}" "cold"
fi

# ---------------------------------------------------------------------------
# [4] Ensure venv exists
if (( ! WARM )); then
    step 4 "Ensure .venv exists"
    t0
    if [[ ! -x "$SCRIPT_DIR/.venv/Scripts/python.exe" ]]; then
        # Try py launcher first, fall back to whatever $PYTHON resolved to.
        if command -v py >/dev/null 2>&1; then
            py -3.12 -m venv "$SCRIPT_DIR/.venv" || die "py -3.12 -m venv failed"
        else
            "$PYTHON" -m venv "$SCRIPT_DIR/.venv" || die "python -m venv failed"
        fi
        ok "created .venv"
    else
        ok ".venv already present"
    fi
    # Switch PYTHON to the venv interpreter for steps 5+.
    PYTHON="$SCRIPT_DIR/.venv/Scripts/python.exe"
    # NEVER pip install --upgrade pip here (knowledge: pip-self-upgrade-breaks-venv).
    info "skipping pip self-upgrade (per knowledge: pip-self-upgrade-breaks-venv)"
    S4_MS="$(t1)"
    record_step 4 ensure-venv 1 "${S4_MS%ms}" "venv ready"
fi

# ---------------------------------------------------------------------------
# [5] Install requirements (idempotent)
if (( ! WARM )); then
    step 5 "Install requirements (-r requirements.txt)"
    t0
    # cd'd to $SCRIPT_DIR at top — use relative path so pip (native Windows tool)
    # doesn't choke on POSIX `/d/...` paths from bash --login -i environments.
    if "$PYTHON" -m pip install --disable-pip-version-check -r requirements.txt >>"$BUILD_LOG" 2>&1; then
        ok "requirements satisfied"
        S5_MS="$(t1)"
        record_step 5 pip-install-req 1 "${S5_MS%ms}" "ok"
    else
        S5_MS="$(t1)"
        record_step 5 pip-install-req 0 "${S5_MS%ms}" "pip exit non-zero (see $BUILD_LOG)"
        die "pip install -r requirements.txt failed (see $BUILD_LOG)"
    fi
    # PyInstaller itself isn't in requirements.txt — install it if missing.
    if ! "$PYTHON" -c "import PyInstaller" >/dev/null 2>&1; then
        info "installing PyInstaller"
        "$PYTHON" -m pip install --disable-pip-version-check pyinstaller >>"$BUILD_LOG" 2>&1 \
            || die "pip install pyinstaller failed (see $BUILD_LOG)"
    fi
fi

# ---------------------------------------------------------------------------
# [6] Tomli-hook workaround (always on cold; never on warm)
if (( ! WARM )); then
    step 6 "Force-reinstall pyinstaller-hooks-contrib"
    t0
    if "$PYTHON" -m pip install --disable-pip-version-check --force-reinstall --no-deps pyinstaller-hooks-contrib >>"$BUILD_LOG" 2>&1; then
        if [[ -f "$HOOK_FILE" ]]; then
            ok "hook-tomli.py present"
            S6_MS="$(t1)"
            record_step 6 hooks-contrib 1 "${S6_MS%ms}" "hook-tomli.py present"
        else
            warn "hook-tomli.py still missing after force-reinstall"
            S6_MS="$(t1)"
            record_step 6 hooks-contrib 0 "${S6_MS%ms}" "hook-tomli.py absent"
        fi
    else
        S6_MS="$(t1)"
        record_step 6 hooks-contrib 0 "${S6_MS%ms}" "pip exit non-zero"
        die "pip force-reinstall pyinstaller-hooks-contrib failed (see $BUILD_LOG)"
    fi
fi

# ---------------------------------------------------------------------------
# [7] PyInstaller build
step 7 "PyInstaller --noconfirm --clean RKOJ.spec"
t0
PY_LOG="$BUILD_LOG_DIR/build-$START_STAMP.log"
# Use a subshell so we can capture exit status while tee'ing.
set +e
"$PYTHON" -m PyInstaller --noconfirm --clean RKOJ.spec 2>&1 | tee -a "$PY_LOG"
PY_RC=${PIPESTATUS[0]}
set -e
if (( PY_RC != 0 )); then
    S7_MS="$(t1)"
    record_step 7 pyinstaller 0 "${S7_MS%ms}" "exit $PY_RC (see $PY_LOG)"
    die "PyInstaller exited $PY_RC (see $PY_LOG)"
fi
ok "PyInstaller succeeded (log: $PY_LOG)"
S7_MS="$(t1)"
record_step 7 pyinstaller 1 "${S7_MS%ms}" "ok"

# ---------------------------------------------------------------------------
# [8] Verify exe artifact
step 8 "Verify dist/RKOJ/RKOJ.exe"
t0
EXE_PATH="$SCRIPT_DIR/dist/RKOJ/RKOJ.exe"
if [[ ! -f "$EXE_PATH" ]]; then
    record_step 8 verify-exe 0 "0" "exe absent"
    die "exe not produced at $EXE_PATH"
fi
# size > 5 MB ?
EXE_SIZE=$(stat -c %s "$EXE_PATH" 2>/dev/null || wc -c <"$EXE_PATH" | tr -d ' ')
if (( EXE_SIZE < 5*1024*1024 )); then
    record_step 8 verify-exe 0 "0" "size=$EXE_SIZE (<5MB)"
    die "exe size $EXE_SIZE bytes is below 5 MB threshold"
fi
# mtime within 5 min ?
NOW_S=$(date +%s)
MTIME_S=$(stat -c %Y "$EXE_PATH" 2>/dev/null || date +%s)
AGE_S=$(( NOW_S - MTIME_S ))
if (( AGE_S > 300 )); then
    record_step 8 verify-exe 0 "0" "stale (${AGE_S}s)"
    die "exe mtime ${AGE_S}s old (>300s) — build likely silently skipped"
fi
ok "exe present, size=$(( EXE_SIZE / 1024 / 1024 )) MB, age=${AGE_S}s"
S8_MS="$(t1)"
record_step 8 verify-exe 1 "${S8_MS%ms}" "size=${EXE_SIZE}B age=${AGE_S}s"

# ---------------------------------------------------------------------------
# [9] Robocopy /MIR -> Desktop (handles locked DLLs; per exe-dll-crash-incomplete-copy)
step 9 "Mirror dist/RKOJ -> Desktop/RKOJ (robocopy)"
t0
SRC_WIN="$(cygpath_w "$SCRIPT_DIR/dist/RKOJ")"
DST_WIN="$(cygpath_w "$DESKTOP_DIR_UNIX")"
mkdir -p "$DESKTOP_DIR_UNIX"
info "src: $SRC_WIN"
info "dst: $DST_WIN"
set +e
# MSYS arg-conversion eats /MIR (-> "C:/Program Files/Git/MIR") AND //MIR
# (robocopy reads it as a UNC path). cmd //c also mangles. PowerShell handles
# native Windows args cleanly — delegate the robocopy there.
# See knowledge: exe-dll-crash-incomplete-copy.md
powershell -NoProfile -Command "& robocopy '$SRC_WIN' '$DST_WIN' /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP; exit \$LASTEXITCODE" >>"$BUILD_LOG" 2>&1
RC_RC=$?
set -e
# robocopy: 0-7 = success (8+ = real failure)
if (( RC_RC > 7 )); then
    record_step 9 robocopy-mirror 0 "0" "rc=$RC_RC"
    die "robocopy failed (rc=$RC_RC); see $BUILD_LOG"
fi
ok "mirror complete (rc=$RC_RC)"
S9_MS="$(t1)"
record_step 9 robocopy-mirror 1 "${S9_MS%ms}" "rc=$RC_RC"

# ---------------------------------------------------------------------------
# [10] Runlog + PROGRESS append + heartbeat (single python one-liner)
step 10 "Runlog + PROGRESS append + heartbeat"
t0
FINISH_ISO="$(utc_iso)"
RUNLOG_PATH="$RUNLOG_DIR/build-rkoj-$START_STAMP.json"
mkdir -p "$RUNLOG_DIR"

# Pipe step log + paths via environment for the python one-liner.
export SANCTUM_BUILD_RUNLOG_PATH="$RUNLOG_PATH"
export SANCTUM_BUILD_STEP_LOG="$STEP_LOG"
export SANCTUM_BUILD_START_ISO="$START_ISO"
export SANCTUM_BUILD_FINISH_ISO="$FINISH_ISO"
export SANCTUM_BUILD_PROGRESS_FILE="$PROGRESS_FILE"
export SANCTUM_BUILD_HEARTBEAT_FILE="$HEARTBEAT_DIR/rkoj-build.beat"
export SANCTUM_BUILD_EXE_PATH="$EXE_PATH"
export SANCTUM_BUILD_EXE_SIZE="$EXE_SIZE"
export SANCTUM_BUILD_LOG="$BUILD_LOG"

"$PYTHON" - <<'PYEOF'
import json, os, datetime, pathlib

runlog_path = os.environ["SANCTUM_BUILD_RUNLOG_PATH"]
step_log    = os.environ["SANCTUM_BUILD_STEP_LOG"]
start_iso   = os.environ["SANCTUM_BUILD_START_ISO"]
finish_iso  = os.environ["SANCTUM_BUILD_FINISH_ISO"]
progress    = os.environ["SANCTUM_BUILD_PROGRESS_FILE"]
heartbeat   = os.environ["SANCTUM_BUILD_HEARTBEAT_FILE"]
exe_path    = os.environ["SANCTUM_BUILD_EXE_PATH"]
exe_size    = int(os.environ.get("SANCTUM_BUILD_EXE_SIZE", "0") or "0")
build_log   = os.environ["SANCTUM_BUILD_LOG"]

steps = []
all_ok = True
with open(step_log, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        n, name, okflag, ms, summary = parts
        try:
            n_i = int(n)
        except ValueError:
            continue
        ok = (okflag == "1")
        if not ok:
            all_ok = False
        try:
            ms_i = int(ms)
        except ValueError:
            ms_i = 0
        steps.append({
            "step": n_i, "name": name, "ok": ok,
            "ms": ms_i, "produced": "", "summary": summary,
        })

manifest = {
    "schema":   "sinister-runlog/v1",
    "script":   "build-rkoj",
    "started":  start_iso,
    "finished": finish_iso,
    "exit_code": 0 if all_ok else 1,
    "ok":        all_ok,
    "steps":     steps,
    "outputs": {
        "exe": exe_path,
        "exe_size_bytes": exe_size,
        "build_log": build_log,
    },
    "warnings": [],
    "errors":   [] if all_ok else ["one or more steps reported failure"],
    "next_actions": [
        "Verify: dist/RKOJ/RKOJ.exe launches",
        "Optional: install Auto-start task via install-console-task.ps1",
    ],
    "auto_close": all_ok,
}

pathlib.Path(runlog_path).parent.mkdir(parents=True, exist_ok=True)
with open(runlog_path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2)
print(f"runlog -> {runlog_path}")

# Append PROGRESS line at the TOP (most-recent-first convention).
stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
size_mb = exe_size / 1024 / 1024 if exe_size else 0
new_line = (
    f"## {stamp} - shipped: RKOJ.exe rebuilt via build-sanctum-console.sh "
    f"({size_mb:.2f} MB; {len(steps)} steps; warm={'1' if any(s['name']=='warm-probe' and 'warm' in s['summary'] for s in steps) else '0'})\n"
    f"Pipeline OK. exe={exe_path}; log={build_log}; runlog={runlog_path}.\n\n"
)
p = pathlib.Path(progress)
if p.exists():
    existing = p.read_text(encoding="utf-8")
    # Insert after the top-level header block (`# Agent: ...\n\nAppend-only ...\n\n---\n\n`).
    marker = "---\n\n"
    idx = existing.find(marker)
    if idx >= 0:
        head = existing[: idx + len(marker)]
        tail = existing[idx + len(marker) :]
        p.write_text(head + new_line + tail, encoding="utf-8")
    else:
        p.write_text(new_line + existing, encoding="utf-8")
    print(f"PROGRESS appended: {progress}")
else:
    print(f"WARN: PROGRESS file missing: {progress}")

# Touch heartbeat.
hb = pathlib.Path(heartbeat)
hb.parent.mkdir(parents=True, exist_ok=True)
hb.write_text(datetime.datetime.utcnow().isoformat() + "Z\n", encoding="utf-8")
print(f"heartbeat -> {heartbeat}")
PYEOF
PY_RC=$?
if (( PY_RC != 0 )); then
    record_step 10 runlog-progress-heartbeat 0 "0" "python exit $PY_RC"
    die "runlog/PROGRESS/heartbeat step exit $PY_RC"
fi
S10_MS="$(t1)"
record_step 10 runlog-progress-heartbeat 1 "${S10_MS%ms}" "manifest+progress+beat"
ok "runlog + PROGRESS + heartbeat written"

# ---------------------------------------------------------------------------
# Final banner
printf '\n  %s================================================================%s\n' "$_C_MAGENTA" "$_C_RESET"
printf '   %sB U I L D   S H I P P E D%s\n' "$_C_GREEN" "$_C_RESET"
printf '   exe:    %s\n' "$EXE_PATH"
printf '   desktop:%s\n' "$DESKTOP_DIR_UNIX/RKOJ.exe"
printf '   log:    %s\n' "$BUILD_LOG"
printf '  %s================================================================%s\n' "$_C_MAGENTA" "$_C_RESET"

exit 0
