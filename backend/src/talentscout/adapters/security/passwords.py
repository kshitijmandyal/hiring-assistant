"""Password hashing with bcrypt.

bcrypt hashes at most the first 72 **bytes** of a password and silently ignores the
rest. Left unchecked, two different long passwords can hash identically, so anything
longer is rejected outright rather than quietly truncated. Note bytes, not characters:
non-ASCII passwords reach the limit sooner than their length suggests.
"""

import bcrypt

from talentscout.constants.auth import (
    BCRYPT_MAX_PASSWORD_BYTES,
    BCRYPT_ROUNDS,
    PASSWORD_MIN_LENGTH,
)
from talentscout.exceptions import WeakPasswordError


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise WeakPasswordError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise WeakPasswordError(
            f"Password must be at most {BCRYPT_MAX_PASSWORD_BYTES} bytes "
            "(shorter if it contains non-ASCII characters)"
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    encoded = password.encode("utf-8")
    # bcrypt 5 raises on an over-long password rather than truncating; a stored hash
    # can never correspond to one, so this is simply a non-match.
    if len(encoded) > BCRYPT_MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(encoded, password_hash.encode("utf-8"))
    except ValueError:
        # Malformed or non-bcrypt hash in the database.
        return False
