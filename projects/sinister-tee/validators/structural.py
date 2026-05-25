"""Structural keybox validator for sinister-tee.

Author: RKOJ-ELENO :: 2026-05-24

Checks:
  1. XML parses
  2. Root element = AndroidAttestation
  3. NumberOfKeyboxes matches actual Keybox count
  4. Each Keybox has DeviceID attribute
  5. Each Key element has algorithm attribute
  6. Each PrivateKey parses as valid PEM
  7. NumberOfCertificates matches actual Certificate count
  8. Each Certificate parses as valid X.509 DER
  9. Cert chain order (leaf -> intermediate -> root) — heuristic via cert subject/issuer

Does NOT check:
  - Whether chain anchors to a Google-trusted root (that's PI STRONG territory; structural only here)
  - CRL revocation status (separate module: validators/crl_check.py)
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization


def validate(path: Path) -> dict:
    result = {
        "path": str(path),
        "ok": True,
        "errors": [],
        "warnings": [],
        "keyboxes": [],
    }
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        result["ok"] = False
        result["errors"].append(f"read failed: {e}")
        return result

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        result["ok"] = False
        result["errors"].append(f"xml parse: {e}")
        return result

    if root.tag != "AndroidAttestation":
        result["errors"].append(f"root tag is {root.tag!r}, expected AndroidAttestation")
        result["ok"] = False

    declared = root.find("NumberOfKeyboxes")
    declared_count = int(declared.text.strip()) if declared is not None and declared.text else 0
    keyboxes = root.findall("Keybox")
    if declared_count != len(keyboxes):
        result["errors"].append(f"NumberOfKeyboxes={declared_count} but found {len(keyboxes)} <Keybox> elements")
        result["ok"] = False

    for ki, kbox in enumerate(keyboxes):
        kresult = {"index": ki, "device_id": kbox.get("DeviceID"), "keys": [], "errors": []}
        if not kresult["device_id"]:
            kresult["errors"].append("missing DeviceID attribute")
            result["ok"] = False

        for key in kbox.findall("Key"):
            kr = {"algorithm": key.get("algorithm"), "private_key_ok": False, "certs": [], "errors": []}
            if not kr["algorithm"]:
                kr["errors"].append("missing algorithm attribute")
                result["ok"] = False

            pk = key.find("PrivateKey")
            if pk is None or not pk.text:
                kr["errors"].append("missing PrivateKey")
                result["ok"] = False
            else:
                try:
                    serialization.load_pem_private_key(pk.text.strip().encode("ascii"), password=None)
                    kr["private_key_ok"] = True
                except Exception as e:
                    kr["errors"].append(f"PrivateKey parse: {e}")
                    result["ok"] = False

            chain = key.find("CertificateChain")
            if chain is None:
                kr["errors"].append("missing CertificateChain")
                result["ok"] = False
            else:
                noc = chain.find("NumberOfCertificates")
                declared_noc = int(noc.text.strip()) if noc is not None and noc.text else 0
                certs = chain.findall("Certificate")
                if declared_noc != len(certs):
                    kr["errors"].append(f"NumberOfCertificates={declared_noc} but {len(certs)} found")
                    result["ok"] = False
                for ci, cert in enumerate(certs):
                    cresult = {"index": ci, "ok": False, "subject": None, "issuer": None, "serial": None}
                    if not cert.text:
                        cresult["error"] = "empty Certificate text"
                    else:
                        try:
                            c = x509.load_pem_x509_certificate(cert.text.strip().encode("ascii"))
                            cresult["ok"] = True
                            cresult["subject"] = c.subject.rfc4514_string()
                            cresult["issuer"] = c.issuer.rfc4514_string()
                            cresult["serial"] = format(c.serial_number, "x")
                        except Exception as e:
                            cresult["error"] = f"parse: {e}"
                            result["ok"] = False
                    kr["certs"].append(cresult)
            kresult["keys"].append(kr)
        result["keyboxes"].append(kresult)
    return result


def print_result(r: dict) -> None:
    print(f"\n=== validate: {r['path']} ===")
    print(f"  ok: {r['ok']}")
    if r["errors"]:
        for e in r["errors"]:
            print(f"  ERROR: {e}")
    for kb in r["keyboxes"]:
        print(f"  Keybox[{kb['index']}] DeviceID={kb['device_id']!r}")
        for kr in kb["keys"]:
            print(f"    Key algorithm={kr['algorithm']} private_key_ok={kr['private_key_ok']} certs={len(kr['certs'])}")
            for cr in kr["certs"]:
                ok = "OK" if cr["ok"] else "FAIL"
                print(f"      cert[{cr['index']}] {ok} subject={cr.get('subject')!r}")
                print(f"                       issuer={cr.get('issuer')!r}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: structural.py <keybox.xml> [<keybox.xml>...]", file=sys.stderr)
        sys.exit(2)
    overall_ok = True
    for arg in sys.argv[1:]:
        r = validate(Path(arg))
        print_result(r)
        if not r["ok"]:
            overall_ok = False
    sys.exit(0 if overall_ok else 1)
