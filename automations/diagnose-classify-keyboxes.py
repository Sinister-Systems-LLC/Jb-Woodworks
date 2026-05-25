#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-24
# Diagnose-lane keybox-OEM classifier — port of panel's keyboxOem.ts logic
# (sinister-panel/source/leo_dev/backend/src/lib/keyboxOem.ts).
#
# Mirrors panel's algorithm:
#   1) DeviceID via regex on <Keybox DeviceID="...">
#   2) Leaf cert = FIRST <Certificate> block (chain order: leaf -> intermediate -> root)
#   3) Subject DN via openssl x509 -noout -subject -nameopt RFC2253
#   4) Classification:
#        Subject DN contains "o=samsung|samsung electronics|o=ses"  -> samsung
#        Subject DN contains "o=google"                              -> google
#        DeviceID matches ^r[a-z0-9]{10}                             -> samsung (heuristic)
#        DeviceID matches ^(ht|hg|9[a-z0-9]{8})                      -> google  (heuristic)
#        else                                                        -> unknown

import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path

def extract_device_id(xml_text):
    m = re.search(r'<Keybox\b[^>]*\bDeviceID="([^"]+)"', xml_text, re.IGNORECASE)
    return m.group(1) if m else None

def extract_leaf_cert_pem(xml_text):
    """First <Certificate>...</Certificate> block, XML-comment lines stripped."""
    m = re.search(r'<Certificate\b[^>]*>\s*([\s\S]*?)\s*</Certificate>', xml_text, re.IGNORECASE)
    if not m:
        return None
    body = m.group(1).strip()
    # Strip any embedded <!-- ... --> comments that pollute the PEM
    body = re.sub(r'<!--[\s\S]*?-->', '', body).strip()
    if "BEGIN CERTIFICATE" not in body:
        body = f"-----BEGIN CERTIFICATE-----\n{body}\n-----END CERTIFICATE-----"
    return body

def get_subject(pem):
    """openssl x509 -noout -subject -nameopt RFC2253 -in <tempfile>."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False, encoding='utf-8') as tf:
        tf.write(pem)
        tf_path = tf.name
    try:
        result = subprocess.run(
            ['openssl', 'x509', '-noout', '-subject', '-issuer', '-enddate', '-nameopt', 'RFC2253', '-in', tf_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None, None, None, result.stderr.strip()
        subject = None
        issuer = None
        end_date = None
        for line in result.stdout.splitlines():
            if line.startswith("subject="):
                subject = line[len("subject="):].strip()
            elif line.startswith("issuer="):
                issuer = line[len("issuer="):].strip()
            elif line.startswith("notAfter="):
                end_date = line[len("notAfter="):].strip()
        return subject, issuer, end_date, None
    finally:
        try:
            os.unlink(tf_path)
        except OSError:
            pass

def classify_oem(device_id, leaf_subject):
    subj = (leaf_subject or "").lower()
    dev = (device_id or "").lower()
    if re.search(r'o=samsung|samsung electronics|o=ses', subj):
        return "samsung", "Subject DN contains Samsung organization"
    if re.search(r'o=google', subj):
        return "google", "Subject DN contains Google organization"
    if re.match(r'^r[a-z0-9]{10}', dev):
        return "samsung", "DeviceID matches Samsung serial prefix (heuristic)"
    if re.match(r'^(ht|hg|9[a-z0-9]{8})', dev):
        return "google", "DeviceID matches Pixel serial prefix (heuristic)"
    return "unknown", (f"Subject DN does not match known OEM patterns: {leaf_subject}" if leaf_subject else "No Subject DN extractable")

def probe(xml_path):
    text = xml_path.read_text(encoding='utf-8', errors='ignore')
    device_id = extract_device_id(text)
    leaf_pem = extract_leaf_cert_pem(text)
    leaf_subject = None
    leaf_issuer = None
    leaf_expiry = None
    parse_error = None
    if leaf_pem:
        subj, iss, end, err = get_subject(leaf_pem)
        if err:
            parse_error = f"cert parse failed: {err}"
        else:
            leaf_subject = subj
            leaf_issuer = iss
            leaf_expiry = end
    else:
        parse_error = "no <Certificate> element found"
    oem, reason = classify_oem(device_id, leaf_subject)
    return {
        "name": xml_path.name,
        "deviceId": device_id,
        "leafSubject": leaf_subject,
        "leafIssuer": leaf_issuer,
        "leafExpiry": leaf_expiry,
        "oem": oem,
        "oemReason": reason,
        "parseError": parse_error,
    }

def main():
    args = sys.argv[1:]
    if not args:
        kbox_dir = Path(r"C:\Users\Zonia\Desktop\Sinister Library Of Alexandria\Sinister RKA\keyboxes-test")
        also = [Path(r"C:\Users\Zonia\Desktop\keybox_20260523.xml")]
    else:
        kbox_dir = Path(args[0])
        also = []
    xmls = sorted(kbox_dir.glob("*.xml")) if kbox_dir.exists() and kbox_dir.is_dir() else []
    xmls.extend(p for p in also if p.exists())
    print(f"Scanning {len(xmls)} XML(s)\n")
    results = []
    for p in xmls:
        r = probe(p)
        results.append(r)
        oem = r['oem']
        marker = ">>>" if oem == "google" else ("XXX" if oem == "samsung" else "   ")
        print(f"{marker} {r['name']:40s} oem={oem:8s}  deviceId={r['deviceId']}")
        print(f"        subject = {r['leafSubject']}")
        print(f"        issuer  = {r['leafIssuer']}")
        print(f"        expiry  = {r['leafExpiry']}")
        print(f"        reason  = {r['oemReason']}")
        if r['parseError']:
            print(f"        ERR     = {r['parseError']}")
        print()
    print("\n=== Pixel-compatible (USE THESE on Pixel 6a) ===")
    found = False
    for r in results:
        if r['oem'] == 'google':
            print(f"  {r['name']}  ({r['leafExpiry']})")
            found = True
    if not found:
        print("  (none — pool has NO Pixel-OEM keyboxes; operator must source one)")
    print("\n=== Samsung (will trigger PI 1/3 on Pixel — DO NOT USE) ===")
    for r in results:
        if r['oem'] == 'samsung':
            print(f"  {r['name']}")
    print("\n=== Unknown ===")
    for r in results:
        if r['oem'] == 'unknown':
            print(f"  {r['name']}  (reason: {r['oemReason'][:80]})")

if __name__ == "__main__":
    main()
