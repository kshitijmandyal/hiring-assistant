"""Authentication constants.

The security model: interviewers authenticate with a password and hold the expensive
capabilities (question generation, grading). Candidates never get an account — they
receive a token scoped to one interview, which can only read questions and submit
answers. That keeps every paid Claude call behind an interviewer.
"""

from enum import StrEnum
from typing import Final

JWT_ALGORITHM: Final = "HS256"
JWT_ISSUER: Final = "talentscout"
# RFC 7518 §3.2: HMAC-SHA256 keys must be at least the hash output size.
JWT_SECRET_MIN_BYTES: Final = 32

ACCESS_TOKEN_TTL_MINUTES: Final = 15
REFRESH_TOKEN_TTL_DAYS: Final = 14
# Long enough that a candidate can finish in their own time, short enough that a
# leaked link stops working.
INVITE_TOKEN_TTL_DAYS: Final = 7

PASSWORD_MIN_LENGTH: Final = 12
# bcrypt ignores everything past 72 bytes, so that is the real ceiling, not a
# policy choice. Longer passwords are rejected rather than silently truncated.
BCRYPT_MAX_PASSWORD_BYTES: Final = 72
PASSWORD_MAX_LENGTH: Final = BCRYPT_MAX_PASSWORD_BYTES

BCRYPT_ROUNDS: Final = 12

BEARER_SCHEME: Final = "Bearer"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    INVITE = "invite"


class Role(StrEnum):
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"
