"""Password hashing — the legacy-migration path is the risky bit.

If verify_password() ever regresses, EVERY existing user is locked out.
"""
import hashlib

import pytest

bcrypt = pytest.importorskip("bcrypt")


def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw, stored):
    if not stored:
        return False, False
    if stored.startswith("$2"):                       # bcrypt
        return bcrypt.checkpw(pw.encode(), stored.encode()), False
    if hashlib.sha256(pw.encode()).hexdigest() == stored:   # legacy
        return True, True                             # ok, needs_upgrade
    return False, False


def test_new_hash_is_bcrypt():
    assert hash_password("hunter2").startswith("$2")


def test_correct_password_verifies():
    ok, upgrade = verify_password("hunter2", hash_password("hunter2"))
    assert ok and not upgrade


def test_wrong_password_rejected():
    ok, _ = verify_password("wrong", hash_password("hunter2"))
    assert not ok


def test_legacy_sha256_user_can_still_log_in():
    """Existing users must NOT be locked out by the bcrypt migration."""
    legacy = hashlib.sha256(b"hunter2").hexdigest()
    ok, needs_upgrade = verify_password("hunter2", legacy)
    assert ok, "legacy user locked out — this would break every existing account"
    assert needs_upgrade, "should be flagged for silent re-hashing"


def test_legacy_wrong_password_still_rejected():
    legacy = hashlib.sha256(b"hunter2").hexdigest()
    ok, _ = verify_password("wrong", legacy)
    assert not ok


def test_salt_makes_identical_passwords_differ():
    assert hash_password("same") != hash_password("same")
