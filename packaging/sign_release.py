# ========== packaging/sign_release.py ==========
# Mikasa AI v8.0.0 — Phase 48: Release Signing & Manifest Automation Tool
# ZERO SECRETS BUNDLED: Private key is loaded exclusively from environment or secure file.
# Signs release artifacts with Ed25519 and updates version_manifest.json.

import os
import sys
import json
import argparse
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sign_release")


def generate_new_keypair() -> Dict[str, str]:
    """Generates an Ed25519 keypair for setting up CI/CD secrets."""
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pub_raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    priv_raw = priv.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption()
    )
    return {
        "public_key_hex": pub_raw.hex().lower(),
        "private_key_hex": priv_raw.hex().lower()
    }


def compute_sha256(filepath: str) -> str:
    """Calculates SHA-256 digest of a local file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def load_private_key(key_hex: Optional[str] = None, key_file: Optional[str] = None) -> ed25519.Ed25519PrivateKey:
    """Loads Ed25519 private key from hex string, file, or environment variable."""
    raw_hex = key_hex or os.environ.get("MIKASA_RELEASE_SIGNING_KEY")
    if not raw_hex and key_file and os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            raw_hex = f.read().strip()

    if not raw_hex:
        raise ValueError(
            "Private signing key not provided. Set MIKASA_RELEASE_SIGNING_KEY env variable "
            "or pass --key-hex or --key-file."
        )

    clean_hex = raw_hex.strip().lower()
    try:
        raw_bytes = bytes.fromhex(clean_hex)
        if len(raw_bytes) != 32:
            raise ValueError(f"Ed25519 private key must be 32 bytes (64 hex characters), got {len(raw_bytes)} bytes")
        return ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)
    except Exception as e:
        raise ValueError(f"Failed to load Ed25519 private key: {e}")


def sign_digest(private_key: ed25519.Ed25519PrivateKey, sha256_hex: str) -> str:
    """Signs canonical SHA-256 hex digest using Ed25519."""
    message_bytes = sha256_hex.strip().lower().encode("utf-8")
    signature_bytes = private_key.sign(message_bytes)
    return signature_bytes.hex().lower()


def update_and_sign_manifest(
    manifest_path: str,
    private_key: ed25519.Ed25519PrivateKey,
    artifacts_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Signs all artifact entries in version_manifest.json."""
    p = Path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(p, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    art_dir = Path(artifacts_dir) if artifacts_dir else p.parent

    # Upgrade / ensure top-level schema fields
    if "channel" not in manifest:
        manifest["channel"] = "stable"
    if "mandatory" not in manifest:
        manifest["mandatory"] = False
    if "minimum_supported_version" not in manifest:
        manifest["minimum_supported_version"] = manifest.get("version", "8.0.0")
    if "release_notes" not in manifest:
        manifest["release_notes"] = [
            "Mikasa AI v8.0.0 Production Release",
            "Secure Ed25519 Auto-Update & Release System",
            "Universal Telegram Webhook Gateway & Remote Control"
        ]

    files_list = manifest.get("files", [])
    signed_count = 0

    for file_entry in files_list:
        fname = file_entry.get("name", "")
        fpath = art_dir / fname
        if fpath.exists():
            computed_sha = compute_sha256(str(fpath))
            file_entry["sha256"] = computed_sha
            file_entry["size_bytes"] = fpath.stat().st_size
            file_entry["size_mb"] = round(fpath.stat().st_size / (1024 * 1024), 2)
        else:
            computed_sha = file_entry.get("sha256", "")

        if computed_sha:
            sig = sign_digest(private_key, computed_sha)
            file_entry["signature"] = sig
            signed_count += 1
            logger.info(f"[Sign] Signed artifact: {fname} (SHA: {computed_sha[:8]}... Sig: {sig[:12]}...)")

    with open(p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"[Sign] Manifest successfully updated and signed ({signed_count} artifacts) at {manifest_path}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Mikasa AI Release Signing & Manifest Automation")
    parser.add_argument("--generate-keypair", action="store_true", help="Generate a new Ed25519 keypair for setup")
    parser.add_argument("--manifest", type=str, help="Path to version_manifest.json to sign")
    parser.add_argument("--artifacts-dir", type=str, help="Directory containing release binaries")
    parser.add_argument("--key-hex", type=str, help="Ed25519 private key in hex (optional, defaults to env var)")
    parser.add_argument("--key-file", type=str, help="Path to file containing Ed25519 private key hex")

    args = parser.parse_args()

    if args.generate_keypair:
        pair = generate_new_keypair()
        print("=== NEW ED25519 RELEASE SIGNING KEYPAIR ===")
        print(f"PUBLIC KEY (client-trusted):  {pair['public_key_hex']}")
        print(f"PRIVATE KEY (CI/CD Secret):   {pair['private_key_hex']}")
        print("NOTE: Store the private key in GitHub Secrets as MIKASA_RELEASE_SIGNING_KEY.")
        print("NEVER commit the private key to Git!")
        return

    if not args.manifest:
        parser.print_help()
        sys.exit(1)

    try:
        priv_key = load_private_key(key_hex=args.key_hex, key_file=args.key_file)
        update_and_sign_manifest(
            manifest_path=args.manifest,
            private_key=priv_key,
            artifacts_dir=args.artifacts_dir
        )
    except Exception as e:
        logger.error(f"[Sign Error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
