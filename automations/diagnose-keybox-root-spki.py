#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-24
# Compute SHA-256 of each keybox ROOT cert's SubjectPublicKeyInfo (SPKI).
# This is the value Play Integrity actually checks against its hard-coded OEM
# root list — Subject DN text is cosmetic; SPKI hash is the cryptographic
# identity. Keyboxes that share an SPKI hash share a root authority.

import os
import re
import sys
import hashlib
import subprocess
import tempfile
from pathlib import Path

def extract_cert_chain(xml_text):
    """Return list of cleaned PEM cert blocks in chain order (leaf -> root)."""
    out = []
    for m in re.finditer(r'<Certificate\b[^>]*>([\s\S]*?)</Certificate>', xml_text, re.IGNORECASE):
        body = m.group(1).strip()
        body = re.sub(r'<!--[\s\S]*?-->', '', body).strip()
        if "BEGIN CERTIFICATE" not in body:
            body = f"-----BEGIN CERTIFICATE-----\n{body}\n-----END CERTIFICATE-----"
        out.append(body)
    return out

def cert_spki_sha256(pem):
    """SHA-256 hex of the cert's SubjectPublicKeyInfo (DER), via openssl chain."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False, encoding='utf-8') as tf:
        tf.write(pem)
        cert_path = tf.name
    try:
        pub = subprocess.run(['openssl', 'x509', '-in', cert_path, '-pubkey', '-noout'],
                             capture_output=True, timeout=10)
        if pub.returncode != 0:
            return None, pub.stderr.decode(errors='ignore').strip()
        der = subprocess.run(['openssl', 'pkey', '-pubin', '-outform', 'DER'],
                             input=pub.stdout, capture_output=True, timeout=10)
        if der.returncode != 0:
            return None, der.stderr.decode(errors='ignore').strip()
        return hashlib.sha256(der.stdout).hexdigest(), None
    finally:
        try:
            os.unlink(cert_path)
        except OSError:
            pass

def cert_subject(pem):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False, encoding='utf-8') as tf:
        tf.write(pem)
        cert_path = tf.name
    try:
        r = subprocess.run(['openssl', 'x509', '-in', cert_path, '-noout', '-subject', '-nameopt', 'RFC2253'],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return None
        for line in r.stdout.splitlines():
            if line.startswith("subject="):
                return line[len("subject="):].strip()
        return None
    finally:
        try:
            os.unlink(cert_path)
        except OSError:
            pass

def main():
    kbox_dir = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Zonia\Desktop\Sinister Library Of Alexandria\Sinister RKA\keyboxes-test")
    extra = [Path(r"C:\Users\Zonia\Desktop\keybox_20260523.xml")]
    xmls = sorted(kbox_dir.glob("*.xml"))
    xmls.extend(p for p in extra if p.exists())
    by_root_spki = {}
    for p in xmls:
        text = p.read_text(encoding='utf-8', errors='ignore')
        chain = extract_cert_chain(text)
        if not chain:
            print(f"{p.name}: NO CERTS")
            continue
        root_pem = chain[-1]
        root_spki, err = cert_spki_sha256(root_pem)
        root_subj = cert_subject(root_pem)
        print(f"{p.name}")
        print(f"  chain_len  = {len(chain)}")
        print(f"  root_subj  = {root_subj}")
        print(f"  root_SPKI  = {root_spki}  err={err}")
        print()
        if root_spki:
            by_root_spki.setdefault(root_spki, []).append(p.name)
    # Group by root SPKI — same SPKI = same OEM root authority
    print("\n=== Keyboxes grouped by root SPKI SHA-256 (same SPKI = same OEM root) ===")
    for i, (spki, names) in enumerate(sorted(by_root_spki.items())):
        print(f"\n  Group {i+1}  root_SPKI={spki}")
        for n in names:
            print(f"    - {n}")
    print(f"\nTotal distinct roots in pool: {len(by_root_spki)}")
    print("\n=== Compare-against-known-OEM-root SHA-256 ===")
    print("Google Hardware Attestation Root (Pixel) SPKI SHA-256 is published by Google;")
    print("operator/panel must fetch it from https://developer.android.com/training/articles/security-key-attestation")
    print("and compare against the Group X SPKI values above. A keybox is")
    print("genuinely Pixel-OEM only if its root SPKI matches Google's HAR.")

if __name__ == "__main__":
    main()
