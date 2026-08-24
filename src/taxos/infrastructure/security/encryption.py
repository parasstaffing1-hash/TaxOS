"""Field-level sensitive data encryption and masking utilities.

Uses AES-256 (Fernet) encryption with key-version tagging for rotation,
controlled exceptions on decryption failure, and no plaintext fallbacks.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Final

from cryptography.fernet import Fernet, InvalidToken

from taxos.core.config import get_settings

CURRENT_KEY_VERSION: Final[str] = "v1"
PAN_LENGTH: Final[int] = 10
AADHAAR_LENGTH: Final[int] = 12


class EncryptionError(Exception):
    """Base exception for cryptographic operations."""


class DecryptionError(EncryptionError):
    """Raised when decryption fails due to invalid key, corrupted token, or missing version."""


def _derive_fernet_key(raw_secret: str) -> bytes:
    """Derive a 32-byte URL-safe base64-encoded Fernet key from a string secret."""
    key_32 = hashlib.sha256(raw_secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_32)


def _get_encryption_cipher(version: str = CURRENT_KEY_VERSION) -> Fernet:
    """Resolve the cryptographic cipher for the requested key version."""
    settings = get_settings()

    # Prefer dedicated FIELD_ENCRYPTION_KEY if provided
    secret: str | None = settings.FIELD_ENCRYPTION_KEY
    if not secret:
        if settings.is_production:
            msg = "FIELD_ENCRYPTION_KEY must be configured in production environment."
            raise EncryptionError(msg)
        secret = str(settings.SECRET_KEY)

    if version == "v1":
        fernet_key = _derive_fernet_key(secret)
        return Fernet(fernet_key)

    msg = f"Unsupported encryption key version: {version}"
    raise EncryptionError(msg)


def encrypt_sensitive_field(
    plain_text: str | None, key_version: str = CURRENT_KEY_VERSION
) -> str | None:
    """Encrypt a sensitive field with key-version prefix (e.g. 'v1:<token>')."""
    if plain_text is None or plain_text == "":
        return None

    cipher = _get_encryption_cipher(version=key_version)
    token_bytes = cipher.encrypt(plain_text.encode("utf-8"))
    token_str = token_bytes.decode("utf-8")
    return f"{key_version}:{token_str}"


def decrypt_sensitive_field(cipher_text: str | None) -> str | None:
    """Decrypt a version-tagged ciphertext field.

    Raises:
        DecryptionError: If the ciphertext is corrupted, uses an unknown key version,
            or fails token authentication.
    """
    if cipher_text is None or cipher_text == "":
        return None

    if ":" not in cipher_text:
        msg = "Ciphertext missing version prefix tag (expected 'v1:<token>')."
        raise DecryptionError(msg)

    version, _, token = cipher_text.partition(":")
    if not version or not token:
        msg = "Malformed encrypted field format."
        raise DecryptionError(msg)

    try:
        cipher = _get_encryption_cipher(version=version)
        decrypted_bytes = cipher.decrypt(token.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken as exc:
        msg = "Decryption failed: Token is invalid or authenticated with wrong key."
        raise DecryptionError(msg) from exc
    except EncryptionError:
        raise
    except Exception as exc:
        msg = f"Decryption failed unexpectedly: {exc}"
        raise DecryptionError(msg) from exc


def mask_pan(pan: str | None) -> str | None:
    """Mask PAN number for safe display (e.g. ABCDE****F)."""
    if not pan or len(pan) != PAN_LENGTH:
        return pan
    return f"{pan[:5]}****{pan[-1]}"


def mask_aadhaar(aadhaar: str | None) -> str | None:
    """Mask 12-digit Aadhaar number for safe display (e.g. **** **** 1234)."""
    if not aadhaar or len(aadhaar.replace(" ", "")) != AADHAAR_LENGTH:
        return aadhaar
    clean = aadhaar.replace(" ", "")
    return f"**** **** {clean[-4:]}"
