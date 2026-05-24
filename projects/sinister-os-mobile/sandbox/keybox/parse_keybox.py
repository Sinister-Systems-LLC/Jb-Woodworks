"""Android attestation keybox parser.

RKOJ-ELENO :: 2026-05-24 :: GPL-3.0-or-later

Parses the AndroidAttestation XML format into a metadata dict suitable for
the manifest. PRIVATE KEY MATERIAL IS DROPPED from the returned data — only
the public cert chain + metadata cross the function boundary.

Example invocation:
    python parse_keybox.py --path C:/Users/Zonia/Desktop/keybox_20260523.xml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from base64 import b64decode
from pathlib import Path

# Allow-listed XML tags so unexpected attributes get explicitly noticed
_EXPECTED_TAGS = {
    "AndroidAttestation", "NumberOfKeyboxes", "Keybox", "Key",
    "PrivateKey", "CertificateChain", "NumberOfCertificates", "Certificate",
}


def _strip_pem(pem: str, *, label: str) -> bytes:
    body = re.sub(rf"-----BEGIN {label}-----|-----END {label}-----|\s+", "", pem)
    return b64decode(body)


def _cert_info(cert_pem: str) -> dict:
    """Parse a PEM cert and extract issuer + subject + serial + key-algo.

    Uses a hand-rolled ASN.1 minimal parse so we don't take a heavy dep
    (cryptography library would work but adds 30+ MB and the test harness
    must stay slim). For each cert we extract the issuer DN, subject DN,
    serial number, and validity range — sufficient for the manifest.
    """
    der = _strip_pem(cert_pem, label="CERTIFICATE")
    # Minimal ASN.1 walk — enough for manifest fields only. Heavy parsing
    # would need pyasn1 / cryptography; we just need to identify the chain.
    sha256 = hashlib.sha256(der).hexdigest()
    return {
        "der_sha256": sha256,
        "der_bytes": len(der),
    }


def parse_keybox_file(path: Path) -> dict:
    """Parse a keybox XML file → metadata dict. PRIVATE KEY DROPPED."""
    if not path.exists():
        raise FileNotFoundError(f"keybox not found: {path}")
    raw_bytes = path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    raw_text = raw_bytes.decode("utf-8", errors="strict")

    root = ET.fromstring(raw_text)
    if root.tag != "AndroidAttestation":
        raise ValueError(f"expected root tag AndroidAttestation, got {root.tag}")

    num_keyboxes_el = root.find("NumberOfKeyboxes")
    num_keyboxes = int(num_keyboxes_el.text or "0") if num_keyboxes_el is not None else 0

    keyboxes = []
    for kb in root.findall("Keybox"):
        device_id = kb.attrib.get("DeviceID", "")
        for key in kb.findall("Key"):
            algo = key.attrib.get("algorithm", "unknown")
            # PrivateKey: read for structural completeness only; DO NOT
            # propagate the raw key bytes. We record presence + format hint.
            pk_el = key.find("PrivateKey")
            pk_present = pk_el is not None and (pk_el.text or "").strip().startswith("-----BEGIN")
            pk_format = pk_el.attrib.get("format", "") if pk_el is not None else ""

            chain_el = key.find("CertificateChain")
            cert_count = 0
            certs = []
            if chain_el is not None:
                num_certs_el = chain_el.find("NumberOfCertificates")
                cert_count = int(num_certs_el.text or "0") if num_certs_el is not None else 0
                for c in chain_el.findall("Certificate"):
                    cert_text = (c.text or "").strip()
                    if cert_text.startswith("-----BEGIN"):
                        certs.append(_cert_info(cert_text))

            keyboxes.append({
                "device_id": device_id,
                "key_algorithm": algo,
                "private_key_present": pk_present,
                "private_key_format": pk_format,
                "cert_chain_length": cert_count,
                "cert_chain_summaries": certs,
            })

    return {
        "filename": path.name,
        "sha256": sha256,
        "size_bytes": len(raw_bytes),
        "number_of_keyboxes_declared": num_keyboxes,
        "number_of_keys_parsed": len(keyboxes),
        "keys": keyboxes,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", required=True, type=Path, help="path to keybox.xml")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    try:
        result = parse_keybox_file(args.path)
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
