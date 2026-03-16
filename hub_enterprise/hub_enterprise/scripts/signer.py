# -*- coding: utf-8 -*-
"""Signature service for skills sync script.

This module wraps the signature generation functionality from
hub_enterprise.signature for use in the sync script.
"""
from pathlib import Path
from typing import Optional

# Import from hub_enterprise.signature
import sys
_hub_path = Path(__file__).parent.parent
if str(_hub_path) not in sys.path:
    sys.path.insert(0, str(_hub_path))

from hub_enterprise.signature import SignatureGenerator, SignatureVerifier, generate_key_pair


class HubSigner:
    """Service for signing skill bundles.

    This class wraps SignatureGenerator to provide a simple interface
    for signing skill bundles during sync operations.
    """

    def __init__(self, private_key_pem: str):
        """Initialize the signer with a private key.

        Args:
            private_key_pem: Private key in PEM format (PKCS8).

        Raises:
            ValueError: If private key is invalid.
        """
        try:
            self.generator = SignatureGenerator(private_key_pem)
        except Exception as e:
            raise ValueError(f"Invalid private key: {e}")

    def sign_bundle(self, bundle: dict) -> str:
        """Generate RSA-PSS signature for a skill bundle.

        Args:
            bundle: Skill bundle data dictionary.

        Returns:
            Base64-encoded signature.

        Raises:
            ValueError: If bundle is invalid or signing fails.
        """
        try:
            return self.generator.sign_skill_bundle(bundle)
        except Exception as e:
            raise ValueError(f"Failed to sign bundle: {e}")

    def get_public_key_pem(self) -> str:
        """Get the public key in PEM format.

        Returns:
            Public key in PEM format.
        """
        return self.generator.get_public_key_pem()


def create_signer(private_key: str | None = None, private_key_file: str | None = None) -> HubSigner:
    """Create a HubSigner instance from key source.

    Args:
        private_key: Private key in PEM format.
        private_key_file: Path to file containing private key.

    Returns:
        Configured HubSigner instance.

    Raises:
        ValueError: If no valid private key is provided.
        FileNotFoundError: If private_key_file doesn't exist.
    """
    key_content: str | None = private_key

    if not key_content and private_key_file:
        key_path = Path(private_key_file)
        if not key_path.exists():
            raise FileNotFoundError(f"Private key file not found: {private_key_file}")
        key_content = key_path.read_text(encoding="utf-8")

    if not key_content:
        raise ValueError(
            "Private key must be provided either directly or via file. "
            "Set HUB_SYNC_PRIVATE_KEY or HUB_SYNC_PRIVATE_KEY_FILE."
        )

    return HubSigner(key_content)


def verify_bundle(
    bundle: dict,
    signature: str,
    public_key_pem: str,
) -> bool:
    """Verify a skill bundle signature.

    Args:
        bundle: Skill bundle data dictionary.
        signature: Base64-encoded signature.
        public_key_pem: Public key in PEM format.

    Returns:
        True if signature is valid, False otherwise.
    """
    verifier = SignatureVerifier(public_key_pem)
    return verifier.verify_skill_bundle(bundle, signature)


def generate_and_save_key_pair(
    output_dir: str | Path | None = None,
    private_key_name: str = "private_key.pem",
    public_key_name: str = "public_key.pem",
) -> tuple[str, str]:
    """Generate and save a new RSA key pair.

    Args:
        output_dir: Directory to save keys. If None, uses current directory.
        private_key_name: Filename for private key.
        public_key_name: Filename for public key.

    Returns:
        Tuple of (private_key_path, public_key_path).
    """
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    private_pem, public_pem = generate_key_pair()

    private_path = output_dir / private_key_name
    public_path = output_dir / public_key_name

    private_path.write_text(private_pem, encoding="utf-8")
    public_path.write_text(public_pem, encoding="utf-8")

    # Set restrictive permissions on private key
    private_path.chmod(0o600)

    return str(private_path), str(public_path)


def print_key_info(private_key_path: str, public_key_path: str) -> None:
    """Print information about generated keys.

    Args:
        private_key_path: Path to private key file.
        public_key_path: Path to public key file.
    """
    print("\n" + "=" * 60)
    print("RSA Key Pair Generated Successfully")
    print("=" * 60)
    print(f"\nPrivate Key: {private_key_path}")
    print(f"  - Keep this file SECRET and secure")
    print(f"  - Use with: HUB_SYNC_PRIVATE_KEY_FILE={private_key_path}")
    print(f"  - Or set as: HUB_SYNC_PRIVATE_KEY=$(cat {private_key_path})")

    print(f"\nPublic Key:  {public_key_path}")
    print(f"  - Distribute this key for signature verification")
    print(f"  - Use with: COPAW_SKILLS_HUB_PUBLIC_KEY=$(cat {public_key_path})")

    print("\n" + "-" * 60)
    print("Security Reminder:")
    print("  - Never commit private keys to version control")
    print("  - Store private keys in secure locations only")
    print("  - Use environment variables for production deployments")
    print("=" * 60 + "\n")
