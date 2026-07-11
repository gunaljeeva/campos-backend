from app.security import hash_password, verify_password


def test_password_hash_roundtrips():
    h = hash_password("s3cret-pw")
    assert h != "s3cret-pw"
    assert verify_password("s3cret-pw", h) is True


def test_wrong_password_fails_verify():
    h = hash_password("s3cret-pw")
    assert verify_password("not-it", h) is False


import pytest
from jose import JWTError
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_reset_token,
    hash_reset_token,
)

UID = "11111111-1111-1111-1111-111111111111"


def test_access_token_encodes_and_decodes():
    tok = create_access_token(UID, 3)
    payload = decode_token(tok, "access")
    assert payload["sub"] == UID
    assert payload["ver"] == 3
    assert payload["type"] == "access"


def test_decode_rejects_wrong_type():
    tok = create_refresh_token(UID, 0)
    with pytest.raises(JWTError):
        decode_token(tok, "access")


def test_decode_rejects_expired(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "access_token_expire_minutes", -1)
    tok = create_access_token(UID, 0)
    with pytest.raises(JWTError):
        decode_token(tok, "access")


def test_reset_token_hash_is_stable_and_matches():
    raw, stored_hash = generate_reset_token()
    assert raw != stored_hash
    assert hash_reset_token(raw) == stored_hash
