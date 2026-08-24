"""Unit tests for Field-level Sensitive Data Encryption and Masking."""

from taxos.infrastructure.security.encryption import (
    decrypt_sensitive_field,
    encrypt_sensitive_field,
    mask_aadhaar,
    mask_pan,
)


def test_pan_masking():
    """Verify PAN masking (e.g. ABCDE1234F -> ABCDE****F)."""
    assert mask_pan("ABCDE1234F") == "ABCDE****F"
    assert mask_pan(None) is None


def test_aadhaar_masking():
    """Verify Aadhaar masking (e.g. 123456789012 -> **** **** 9012)."""
    assert mask_aadhaar("1234 5678 9012") == "**** **** 9012"
    assert mask_aadhaar("123456789012") == "**** **** 9012"
    assert mask_aadhaar(None) is None


def test_sensitive_field_encryption_roundtrip():
    """Verify encryption and decryption roundtrip for sensitive strings."""
    plain = "AAAPA1234C"
    encrypted = encrypt_sensitive_field(plain)
    assert encrypted is not None
    assert encrypted != plain

    decrypted = decrypt_sensitive_field(encrypted)
    assert decrypted == plain
