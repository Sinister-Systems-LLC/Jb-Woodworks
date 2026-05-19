# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# _build-helpers.sh — shared bash idioms for the Sanctum-Console build pipeline.
# Source this from build-sanctum-console.sh; do not execute directly.
#
# Provides:
#   step "<n>" "<title>"      — print a colored phase banner
#   ok "<msg>"                — green [OK]
#   warn "<msg>"              — yellow [WARN]
#   fail "<msg>"              — red [FAIL]
#   info "<msg>"              — dim gray detail line
#   die "<msg>" [exit-code]   — fail + exit (default code 1)
#   t0                        — record monotonic start (epoch-ns)
#   t1                        — print elapsed ms since last t0
#   cygpath_w "<unix-path>"   — convert /c/Users/... -> C:\Users\...
#   utc_stamp                 — UTC ISO timestamp 20260519T040700Z style
#   require_cmd "<cmd>"       — die if cmd not on PATH
#
# Idiom port table (PowerShell -> bash):
#   Step $n $name                       -> step "$n" "$name"
#   Out-OK $msg                         -> ok "$msg"
#   Out-WARN $msg                       -> warn "$msg"
#   Out-FAIL $msg                       -> fail "$msg"
#   Out-INFO $msg                       -> info "$msg"
#   $ErrorActionPreference = 'Stop'     -> set -euo pipefail (caller responsibility)

# Color helpers — degrade to plain text when not a TTY (e.g. piped to tee).
if [[ -t 1 ]]; then
    _C_RESET=$'\033[0m'
    _C_RED=$'\033[31m'
    _C_GREEN=$'\033[32m'
    _C_YELLOW=$'\033[33m'
    _C_CYAN=$'\033[36m'
    _C_MAGENTA=$'\033[35m'
    _C_DIM=$'\033[2m'
    _C_BOLD=$'\033[1m'
else
    _C_RESET=''
    _C_RED=''
    _C_GREEN=''
    _C_YELLOW=''
    _C_CYAN=''
    _C_MAGENTA=''
    _C_DIM=''
    _C_BOLD=''
fi

step() {
    local n="$1"; shift
    local title="$*"
    printf '\n%s[%s] %s%s\n' "$_C_CYAN" "$n" "$title" "$_C_RESET"
}

ok()   { printf '    %s[OK]%s %s\n' "$_C_GREEN" "$_C_RESET" "$*"; }
warn() { printf '    %s[WARN]%s %s\n' "$_C_YELLOW" "$_C_RESET" "$*"; }
fail() { printf '    %s[FAIL]%s %s\n' "$_C_RED" "$_C_RESET" "$*"; }
info() { printf '    %s%s%s\n' "$_C_DIM" "$*" "$_C_RESET"; }

die() {
    local msg="$1"
    local code="${2:-1}"
    fail "$msg"
    exit "$code"
}

# Monotonic timing via date +%s%N (git-bash supports it).
# Fallback to %s (whole seconds) if nanoseconds unavailable.
_T0_NS=0
t0() {
    if date +%s%N >/dev/null 2>&1; then
        _T0_NS=$(date +%s%N)
    else
        _T0_NS=$(( $(date +%s) * 1000000000 ))
    fi
}

t1() {
    local now_ns end_ns ms
    if date +%s%N >/dev/null 2>&1; then
        end_ns=$(date +%s%N)
    else
        end_ns=$(( $(date +%s) * 1000000000 ))
    fi
    now_ns="$end_ns"
    ms=$(( (now_ns - _T0_NS) / 1000000 ))
    printf '%sms' "$ms"
}

# Convert /c/Users/Zonia/foo -> C:\Users\Zonia\foo for native Windows tools
# (robocopy, PyInstaller log paths, etc.). Use git-bash's cygpath if present.
cygpath_w() {
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -w "$1"
    else
        # Fallback: best-effort manual conversion (covers /c/, /d/, ...).
        echo "$1" | sed -E 's|^/([a-zA-Z])/|\1:/|' | tr '/' '\\'
    fi
}

# UTC stamp suitable for filenames + runlog "started"/"finished" fields.
utc_stamp() {
    date -u +%Y%m%dT%H%M%SZ
}

# Like utc_stamp but ISO-8601 with colons (matches sinister-runlog/v1 sample).
utc_iso() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        die "required command not on PATH: $cmd"
    fi
}
