"""What must never reach a log line."""

from typing import Final

# Scrubbed from log record extras by RedactingFilter. Identifiers are included
# deliberately: correlating a candidate row to a person is exactly what logs must not enable.
SENSITIVE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "candidate_id",
        "interview_id",
        "email",
        "phone",
        "phone_number",
        "full_name",
        "name",
        "location",
        "answer",
        "answer_text",
        "api_key",
        "authorization",
        "password",
        "token",
    }
)

CORRELATION_ID_LENGTH: Final = 8
