# -*- coding: utf-8 -*-
"""Signature generation and verification module.

This module provides cryptographic signing capabilities for skill bundles
using RSA keys with PSS padding and SHA-256 hashing.
"""
import hashlib
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


class SignatureGenerator:
    """Signature generator for skill bundles."""

    def __init__(self, private_key_pem: str):
        """Initialize with a private key in PEM format.

        Args:
            private_key_pem: Private key in PEM format (PKCS8).
        """
        self.private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend(),
        )

    def sign_skill_bundle(self, bundle: dict) -> str:
        """Sign a skill bundle.

        Args:
            bundle: Skill bundle data dictionary.

        Returns:
            Base64-encoded signature.
        """
        bundle_hash = self._hash_bundle(bundle)
        signature = self.private_key.sign(
            bundle_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def get_public_key_pem(self) -> str:
        """Get the public key in PEM format.

        Returns:
            Public key in PEM format.
        """
        public_key = self.private_key.public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem.decode()

    def _hash_bundle(self, bundle: dict) -> bytes:
        """Calculate the hash of a skill bundle.

        Args:
            bundle: Skill bundle data dictionary.

        Returns:
            SHA-256 hash of the normalized bundle.
        """
        normalized = json.dumps(
            bundle,
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(normalized.encode()).digest()


class SignatureVerifier:
    """Signature verifier for skill bundles."""

    def __init__(self, public_key_pem: str):
        """Initialize with a public key in PEM format.

        Args:
            public_key_pem: Public key in PEM format.
        """
        self.public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend(),
        )

    def verify_skill_bundle(
        self,
        bundle: dict,
        signature: str,
    ) -> bool:
        """Verify a skill bundle signature.

        Args:
            bundle: Skill bundle data dictionary.
            signature: Base64-encoded signature.

        Returns:
            True if signature is valid, False otherwise.
        """
        try:
            bundle_hash = self._hash_bundle(bundle)
            signature_bytes = base64.b64decode(signature)
            self.public_key.verify(
                signature_bytes,
                bundle_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    def _hash_bundle(self, bundle: dict) -> bytes:
        """Calculate the hash of a skill bundle.

        Args:
            bundle: Skill bundle data dictionary.

        Returns:
            SHA-256 hash of the normalized bundle.
        """
        normalized = json.dumps(
            bundle,
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(normalized.encode()).digest()


def generate_key_pair() -> tuple[str, str]:
    """Generate a new RSA key pair.

    Returns:
        Tuple of (private_key_pem, public_key_pem).
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    return private_pem, public_pem
