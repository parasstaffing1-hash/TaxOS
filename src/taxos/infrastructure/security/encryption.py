"""Field-level sensitive data encryption utilities (AES-256 / Fernet)."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from taxos.core.config import get_settings


def _get_encryption_cipher() -> Fernet:
    """Derive deterministic Fernet encryption key from application secret key."""
    settings = get_settings()
    secret = str(settings.SECRET_KEY)
    # Generate 32-byte key from SHA256 of secret
    key_32 = hashlib.sha256(secret.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_32)
    return Fernet(fernet_key)


def encrypt_sensitive_field(plain_text: str | None) -> str | None:
    """Encrypt a sensitive field (e.g. PAN, Aadhaar, Bank Account)."""
    if not plain_text:
        return None
    cipher = _get_encryption_cipher()
    encrypted_bytes = cipher.encrypt(plain_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_sensitive_field(cipher_text: str | None) -> str | None:
    """Decrypt a previously encrypted field."""
    if not cipher_text:
        return None
    try:
        cipher = _get_encryption_cipher()
        decrypted_bytes = cipher.decrypt(cipher_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # Fallback if text is not encrypted (plain text backward compatibility)
        return cipher_text


PAN_LENGTH = 10
AADHAAR_LENGTH = 12


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

