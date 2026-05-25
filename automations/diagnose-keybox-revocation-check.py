#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-24
# Cross-reference each keybox's full cert chain serials against Google's
# Hardware Attestation revocation list (https://android.googleapis.com/attestation/status).
# Google keys the revocation list by decimal cert serial. PI verdict
# downgrades to BASIC (1/3) when ANY cert in the leaf-to-root chain is in
# the revocation list with status=REVOKED.

import os
import re
import sys
import json
import subprocess
import tempfile
from pathlib import Path

import tempfile as _tempfile
STATUS_PATH = os.environ.get("ATTEST_STATUS", os.path.join(_tempfile.gettempdir(), "google_attest_status.json"))

def load_revocation_list():
    with open(STATUS_PATH, "r") as f:
        data = json.load(f)
    return data.get("entries", {})

def extract_cert_chain(xml_text):
    out = []
    for m in re.finditer(r'<Certificate\b[^>]*>([\s\S]*?)</Certificate>', xml_text, re.IGNORECASE):
        body = m.group(1).strip()
        body = re.sub(r'<!--[\s\S]*?-->', '', body).strip()
        if "BEGIN CERTIFICATE" not in body:
            body = f"-----BEGIN CERTIFICATE-----\n{body}\n-----END CERTIFICATE-----"
        out.append(body)
    return out

def cert_serial_hex(pem):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False, encoding='utf-8') as tf:
        tf.write(pem)
        cert_path = tf.name
    try:
        r = subprocess.run(['openssl', 'x509', '-in', cert_path, '-noout', '-serial'],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return None
        for line in r.stdout.splitlines():
            if line.startswith("serial="):
                return line[len("serial="):].strip().lower()
        return None
    finally:
        try: os.unlink(cert_path)
        except OSError: pass

def cert_subject(pem):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False, encoding='utf-8') as tf:
        tf.write(pem)
        cert_path = tf.name
    try:
        r = subprocess.run(['openssl', 'x509', '-in', cert_path, '-noout', '-subject', '-nameopt', 'RFC2253'],
                           capture_output=True, text=True, timeout=10)
        for line in r.stdout.splitlines():
            if line.startswith("subject="):
                return line[len("subject="):].strip()
        return None
    finally:
        try: os.unlink(cert_path)
        except OSError: pass

def hex_to_decimal(hex_str):
    return str(int(hex_str.replace(":", "").replace(" ", ""), 16))

def main():
    revocation = load_revocation_list()
    print(f"Loaded {len(revocation)} revocation entries from Google attestation status list\n")
    kbox_dir = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Zonia\Desktop\Sinister Library Of Alexandria\Sinister RKA\keyboxes-test")
    extras = [Path(r"C:\Users\Zonia\Desktop\keybox_20260523.xml")]
    xmls = sorted(kbox_dir.glob("*.xml"))
    xmls.extend(p for p in extras if p.exists())
    for p in xmls:
        text = p.read_text(encoding='utf-8', errors='ignore')
        chain = extract_cert_chain(text)
        if not chain:
            print(f"{p.name}: NO CERTS"); continue
        print(f"\n{p.name}  (chain len {len(chain)}):")
        any_revoked = False
        for i, pem in enumerate(chain):
            label = "leaf" if i == 0 else ("root" if i == len(chain)-1 else f"int{i}")
            hex_serial = cert_serial_hex(pem)
            if not hex_serial:
                print(f"  [{label}] serial=?  (parse failed)")
                continue
            try:
                dec_serial = hex_to_decimal(hex_serial)
            except Exception:
                print(f"  [{label}] serial=0x{hex_serial} (decimal-conv failed)")
                continue
            rev = revocation.get(dec_serial)
            status = "**REVOKED**" if rev else "ok"
            reason = f" reason={rev['reason']}" if rev else ""
            if rev: any_revoked = True
            subj = cert_subject(pem)
            print(f"  [{label}] serial=0x{hex_serial} (decimal {dec_serial})  {status}{reason}")
            print(f"           subject = {subj}")
        print(f"  ==> verdict: {'REVOKED chain — PI will be BASIC (1/3)' if any_revoked else 'CHAIN CLEAN — PI eligible for STRONG (3/3) IF root matches Google HAR'}")

if __name__ == "__main__":
    main()
