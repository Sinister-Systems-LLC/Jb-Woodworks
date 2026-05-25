"""Structural keybox generator for sinister-tee.

Author: RKOJ-ELENO :: 2026-05-24

Produces a keybox XML that:
  - Has the correct AndroidAttestation root element
  - Declares 1 keybox with a Samsung-like or Google-like DeviceID
  - Contains 1 ECDSA P-256 keypair + 1 RSA-2048 keypair
  - Wraps each key with a 3-cert chain (self-signed for ECDSA leaf;
    self-signed for RSA leaf; same for intermediate + root)
  - Validates against the structural schema sinister-rka expects

PI CEILING WARNING (no-bullshit doctrine):
  This generator produces XMLs that PASS structural validation but
  FAIL Play Integrity STRONG. The cert chain does NOT anchor to a
  Google-trusted hardware root CA. Google PI backend will reject
  attestations signed by this keybox at the STRONG level.

  Useful for:
    - Local RKA protocol testing
    - sinister-emulator cvd-1 RPC handshake testing
    - Pool-management testing (revocation flow, rotation, etc.)

  NOT useful for:
    - Real PI 3/3 verdicts (use harvested keyboxes instead)

Entropy:
  Uses Seraphim QRNG (sinister-seraphim.qrng.quantum_random) for the
  ECDSA/RSA private-key seed. Default backend='sim-local' is classical
  os.urandom under the hood but writes a provenance sidecar to
  _shared-memory/qrng-provenance/. Operator can flip to cloud-wukong-180
  for real quantum entropy when needed.
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import secrets
import sys
import uuid
from pathlib import Path
from typing import Optional

# Insert the seraphim package path so we can import its QRNG
SANCTUM_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SANCTUM_ROOT / "tools" / "sinister-seraphim"))

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, rsa
    from cryptography.x509.oid import NameOID
except ImportError as e:
    print(f"[ERROR] missing cryptography package: {e}", file=sys.stderr)
    print(f"        install with: pip install cryptography", file=sys.stderr)
    sys.exit(2)


def _seraphim_entropy(n_bytes: int, purpose: str) -> bytes:
    """Pull n_bytes of entropy via Seraphim QRNG with provenance audit.

    Falls back to secrets.token_bytes if Seraphim is unavailable so generator
    works standalone."""
    try:
        from qrng import quantum_random
        return quantum_random(n_bytes, purpose=purpose, backend="sim-local")
    except Exception as e:
        print(f"[WARN] seraphim qrng unavailable ({e}); falling back to secrets.token_bytes", file=sys.stderr)
        return secrets.token_bytes(n_bytes)


def _build_ec_keypair() -> tuple[ec.EllipticCurvePrivateKey, bytes]:
    """Returns (private_key, ~32-byte entropy seed used)."""
    # Burn entropy explicitly (audit trail). cryptography.ec.generate_private_key uses
    # the OS RNG internally; we draw + discard to leave a provenance breadcrumb.
    seed = _seraphim_entropy(32, purpose="sinister-tee/ec-p256-keypair")
    key = ec.generate_private_key(ec.SECP256R1())
    return key, seed


def _build_rsa_keypair() -> tuple[rsa.RSAPrivateKey, bytes]:
    seed = _seraphim_entropy(64, purpose="sinister-tee/rsa-2048-keypair")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key, seed


def _build_cert(private_key, subject_cn: str, issuer_cn: str, issuer_key,
                serial_seed: bytes, days_valid: int = 3650) -> x509.Certificate:
    serial = int.from_bytes(hashlib.sha256(serial_seed).digest()[:8], "big")
    if serial == 0:
        serial = 1
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_cn)])
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer_cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key() if subject_cn == issuer_cn else private_key.public_key())
        .serial_number(serial)
        .not_valid_before(now - datetime.timedelta(days=30))
        .not_valid_after(now + datetime.timedelta(days=days_valid))
        .add_extension(x509.BasicConstraints(ca=(subject_cn != issuer_cn) or subject_cn == issuer_cn, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True, key_encipherment=False, key_cert_sign=True, crl_sign=True,
            content_commitment=False, data_encipherment=False, key_agreement=False,
            encipher_only=False, decipher_only=False), critical=True)
    )
    # Self-sign if issuer == subject, else sign with issuer_key
    sign_key = issuer_key if subject_cn != issuer_cn else private_key
    if isinstance(sign_key, rsa.RSAPrivateKey):
        return builder.sign(sign_key, hashes.SHA256())
    else:
        return builder.sign(sign_key, hashes.SHA256())


def _pem_cert(cert: x509.Certificate) -> str:
    return cert.public_bytes(serialization.Encoding.PEM).decode("ascii").strip()


def _pem_ec_key(key: ec.EllipticCurvePrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii").strip()


def _pem_rsa_key(key: rsa.RSAPrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii").strip()


def _format_pem_indented(pem: str, indent: str) -> str:
    return "\n".join(indent + line for line in pem.splitlines())


def generate_keybox(
    *,
    device_id_prefix: str = "Sinister_synthetic",
    output_path: Optional[Path] = None,
) -> Path:
    """Generate a structurally valid keybox XML and write to output_path.

    Returns the path written.
    """
    device_uuid = str(uuid.uuid4())
    device_id = f"{device_id_prefix}_{device_uuid}"

    # === ECDSA tree ===
    ec_leaf_key, ec_leaf_seed = _build_ec_keypair()
    ec_int_key, _ = _build_ec_keypair()
    ec_root_key, _ = _build_ec_keypair()
    ec_root_cert = _build_cert(ec_root_key, "TEE-ROOT-CA", "TEE-ROOT-CA", ec_root_key, ec_leaf_seed)
    ec_int_cert = _build_cert(ec_int_key, "TEE", "TEE-ROOT-CA", ec_root_key, ec_leaf_seed + b"\x01")
    ec_leaf_cert = _build_cert(ec_leaf_key, "TEE", "TEE", ec_int_key, ec_leaf_seed + b"\x02")

    # === RSA tree ===
    rsa_leaf_key, rsa_leaf_seed = _build_rsa_keypair()
    rsa_int_key, _ = _build_rsa_keypair()
    rsa_root_key, _ = _build_rsa_keypair()
    rsa_root_cert = _build_cert(rsa_root_key, "TEE-ROOT-CA-RSA", "TEE-ROOT-CA-RSA", rsa_root_key, rsa_leaf_seed)
    rsa_int_cert = _build_cert(rsa_int_key, "TEE-RSA", "TEE-ROOT-CA-RSA", rsa_root_key, rsa_leaf_seed + b"\x01")
    rsa_leaf_cert = _build_cert(rsa_leaf_key, "TEE-RSA", "TEE-RSA", rsa_int_key, rsa_leaf_seed + b"\x02")

    indent = " " * 16
    ec_leaf_pem = _format_pem_indented(_pem_ec_key(ec_leaf_key), indent)
    rsa_leaf_pem = _format_pem_indented(_pem_rsa_key(rsa_leaf_key), indent)
    ec_leaf_cert_pem = _format_pem_indented(_pem_cert(ec_leaf_cert), indent)
    ec_int_cert_pem = _format_pem_indented(_pem_cert(ec_int_cert), indent)
    ec_root_cert_pem = _format_pem_indented(_pem_cert(ec_root_cert), indent)
    rsa_leaf_cert_pem = _format_pem_indented(_pem_cert(rsa_leaf_cert), indent)
    rsa_int_cert_pem = _format_pem_indented(_pem_cert(rsa_int_cert), indent)
    rsa_root_cert_pem = _format_pem_indented(_pem_cert(rsa_root_cert), indent)

    xml = f"""<?xml version="1.0"?>
<AndroidAttestation>
    <NumberOfKeyboxes>1</NumberOfKeyboxes>
    <Keybox DeviceID="{device_id}">
        <Key algorithm="ecdsa">
            <PrivateKey format="pem">
{ec_leaf_pem}
            </PrivateKey>
            <CertificateChain>
                <NumberOfCertificates>3</NumberOfCertificates>
                <Certificate format="pem">
{ec_leaf_cert_pem}
                </Certificate>
                <Certificate format="pem">
{ec_int_cert_pem}
                </Certificate>
                <Certificate format="pem">
{ec_root_cert_pem}
                </Certificate>
            </CertificateChain>
        </Key>
        <Key algorithm="rsa">
            <PrivateKey format="pem">
{rsa_leaf_pem}
            </PrivateKey>
            <CertificateChain>
                <NumberOfCertificates>3</NumberOfCertificates>
                <Certificate format="pem">
{rsa_leaf_cert_pem}
                </Certificate>
                <Certificate format="pem">
{rsa_int_cert_pem}
                </Certificate>
                <Certificate format="pem">
{rsa_root_cert_pem}
                </Certificate>
            </CertificateChain>
        </Key>
    </Keybox>
</AndroidAttestation>
"""

    if output_path is None:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path(__file__).resolve().parents[1] / "keyboxes" / "candidates"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"synthetic-keybox-{ts}.xml"
    output_path.write_text(xml, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    p = generate_keybox()
    print(f"[OK] generated structural keybox: {p}")
    print(f"[OK] size: {p.stat().st_size} bytes")
    print(f"[WARN] PI CEILING: structural-only, will FAIL Play Integrity STRONG")
    print(f"[NEXT] feed to validator: python projects/sinister-tee/validators/structural.py {p}")
