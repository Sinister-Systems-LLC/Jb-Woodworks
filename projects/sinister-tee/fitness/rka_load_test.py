"""Load a keybox candidate against a fresh local RKA server, capture result.

Author: RKOJ-ELENO :: 2026-05-24

Spin up the Java RKA server pointing at the keybox under test, wait, parse
stderr for ACTIVE/SUSPENDED/error markers, terminate. Records result to the
keyboxes/<state>/ pool directory.

Outputs:
  exit code 0 -> keybox loaded ACTIVE
  exit code 1 -> structural valid but rejected by server
  exit code 2 -> hard error (server didn't start, etc.)

This is the FITNESS test stage. It does NOT test PI verdict. PI verdict
requires the operator to deploy the keybox via sinister-rka to a real phone
or to cvd-1 booted with libsinister_attest.so. This stage's value is:
"the local RKA server can serve attestations using this keybox".
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

JAVA = r"C:\Program Files\Java\jdk-25\bin\java.exe"
REPO = r"C:\Users\Zonia\Desktop\Sinister RKA GOOD\server-java"
ALT_PORT = 59361  # avoid yk50:59347 + emu-test:59348 + emu-alt:59351


def run_load_test(keybox_path: Path, timeout: int = 8) -> dict:
    out_log = Path("C:\\Users\\Zonia\\AppData\\Local\\Temp") / f"sinister-tee-load-{keybox_path.stem}.log"
    err_log = Path(str(out_log) + ".err")
    if out_log.exists():
        out_log.unlink()
    if err_log.exists():
        err_log.unlink()
    fh_out = out_log.open("wb")
    fh_err = err_log.open("wb")
    proc = subprocess.Popen(
        [JAVA, "-cp", "out;libs/*", "com.sinister.rka.server.Main",
         "--keybox", str(keybox_path), "--port", str(ALT_PORT), "--bind", "127.0.0.1"],
        cwd=REPO, stdout=fh_out, stderr=fh_err,
    )
    try:
        # Wait for ACTIVE / SUSPENDED / error marker
        start = time.time()
        marker = None
        log_text = ""
        while time.time() - start < timeout:
            time.sleep(0.5)
            try:
                log_text = err_log.read_text(encoding="utf-8", errors="replace")
            except Exception:
                log_text = ""
            if re.search(r"\bACTIVE\b", log_text):
                marker = "ACTIVE"
                break
            if re.search(r"\bSUSPENDED\b", log_text):
                marker = "SUSPENDED"
                break
            if re.search(r"Exception|FATAL|❌", log_text):
                marker = "ERROR"
                break
        # If still nothing after timeout, mark unknown
        if marker is None:
            marker = "TIMEOUT"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        fh_out.close()
        fh_err.close()

    # Final log read
    try:
        log_text = err_log.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Extract cert count + algo if loaded
    algo_match = re.search(r"keybox loaded:.*?\((\d+) certs, algo=(\w+)\)", log_text)
    cert_count = int(algo_match.group(1)) if algo_match else None
    algo = algo_match.group(2) if algo_match else None
    revoked_match = re.search(r"CRL probe: (\d+) revoked entries total, (\d+) active keyboxes checked, (\d+) new suspensions", log_text)
    suspensions = int(revoked_match.group(3)) if revoked_match else None
    return {
        "keybox": str(keybox_path),
        "marker": marker,
        "cert_count": cert_count,
        "algo": algo,
        "crl_new_suspensions": suspensions,
        "log_path": str(err_log),
    }


def classify_and_move(keybox_path: Path, result: dict) -> Path:
    """Move keybox to the appropriate pool directory based on result."""
    project_root = keybox_path.resolve().parents[1]
    if result["marker"] == "ACTIVE" and (result["crl_new_suspensions"] or 0) == 0:
        target = project_root / "harvested" / keybox_path.name
    elif result["marker"] == "SUSPENDED" or (result["crl_new_suspensions"] or 0) > 0:
        target = project_root / "revoked" / keybox_path.name
    else:
        target = keybox_path  # leave in place for inspection
    if target != keybox_path:
        target.parent.mkdir(parents=True, exist_ok=True)
        keybox_path.rename(target)
    return target


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: rka_load_test.py <keybox.xml> [<keybox.xml>...]", file=sys.stderr)
        sys.exit(2)
    overall = 0
    for arg in sys.argv[1:]:
        p = Path(arg).resolve()
        if not p.exists():
            print(f"[ERROR] not found: {p}", file=sys.stderr)
            overall = 2
            continue
        r = run_load_test(p)
        print(f"\n=== {p.name} ===")
        print(f"  marker: {r['marker']}")
        print(f"  algo: {r['algo']}  certs: {r['cert_count']}")
        print(f"  crl_new_suspensions: {r['crl_new_suspensions']}")
        print(f"  log: {r['log_path']}")
        moved = classify_and_move(p, r)
        if moved != p:
            print(f"  moved: {p.parent.name}/ -> {moved.parent.name}/{moved.name}")
        if r["marker"] != "ACTIVE":
            overall = max(overall, 1)
    sys.exit(overall)
