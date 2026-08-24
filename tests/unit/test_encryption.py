"""Unit tests for Field-level Sensitive Data Encryption, Key Versioning, and Masking."""

import pytest
from cryptography.fernet import Fernet

from taxos.core.config import Settings
from taxos.infrastructure.security.encryption import (
    DecryptionError,
    decrypt_sensitive_field,
    encrypt_sensitive_field,
    mask_aadhaar,
    mask_pan,
)


def test_pan_masking():
    """Verify PAN masking (e.g. ABCDE1234F -> ABCDE****F)."""
    assert mask_pan("ABCDE1234F") == "ABCDE****F"
    assert mask_pan(None) is None
    assert mask_pan("INVALID") == "INVALID"


def test_aadhaar_masking():
    """Verify Aadhaar masking (e.g. 123456789012 -> **** **** 9012)."""
    assert mask_aadhaar("1234 5678 9012") == "**** **** 9012"
    assert mask_aadhaar("123456789012") == "**** **** 9012"
    assert mask_aadhaar(None) is None
    assert mask_aadhaar("123") == "123"


def test_sensitive_field_encryption_roundtrip():
    """Verify encryption and decryption roundtrip with version prefix."""
    plain = "AAAPA1234C"
    encrypted = encrypt_sensitive_field(plain)
    assert encrypted is not None
    assert encrypted.startswith("v1:")
    assert encrypted != plain

    decrypted = decrypt_sensitive_field(encrypted)
    assert decrypted == plain


def test_empty_or_none_encryption():
    """Verify None and empty strings return None without errors."""
    assert encrypt_sensitive_field(None) is None
    assert encrypt_sensitive_field("") is None
    assert decrypt_sensitive_field(None) is None
    assert decrypt_sensitive_field("") is None


def test_decryption_missing_version_tag_raises():
    """Verify plaintext or missing version tag raises DecryptionError."""
    with pytest.raises(DecryptionError, match="missing version prefix"):
        decrypt_sensitive_field("raw_unencrypted_pan_or_text")


def test_decryption_corrupted_ciphertext_raises():
    """Verify corrupted token raises DecryptionError without leaking plaintext."""
    with pytest.raises(DecryptionError):
        decrypt_sensitive_field("v1:not_a_valid_fernet_token_xyz")


def test_decryption_wrong_key_raises():
    """Verify token encrypted with a different key fails to decrypt with DecryptionError."""
    foreign_key = Fernet.generate_key()
    foreign_cipher = Fernet(foreign_key)
    foreign_token = foreign_cipher.encrypt(b"SECRET_DATA").decode("utf-8")

    with pytest.raises(DecryptionError, match="Decryption failed"):
        decrypt_sensitive_field(f"v1:{foreign_token}")


def test_production_settings_validation_for_encryption_key():
    """Verify production settings fail closed if FIELD_ENCRYPTION_KEY is missing."""
    with pytest.raises(ValueError, match="FIELD_ENCRYPTION_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            ALLOWED_ORIGINS=["https://app.taxos.com"],
            # FIELD_ENCRYPTION_KEY missing!
        )

    # Valid when configured
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 32,
        FIELD_ENCRYPTION_KEY="b" * 32,
        ALLOWED_ORIGINS=["https://app.taxos.com"],
    )
    assert prod_settings.FIELD_ENCRYPTION_KEY == "b" * 32
