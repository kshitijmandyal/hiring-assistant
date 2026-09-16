"""Validated primitives.

Validation lives in the type rather than at call sites, so an invalid Candidate
cannot be constructed at all — the previous implementation validated advisorily
and stored the bad record anyway.
"""

from typing import Annotated, Any

import phonenumbers
from pydantic import AfterValidator, EmailStr, Field, StringConstraints

from talentscout.constants import (
    ANSWER_MAX_LENGTH,
    ANSWER_MIN_LENGTH,
    TECH_STACK_MAX_SIZE,
    TECHNOLOGY_NAME_MAX_LENGTH,
    YEARS_OF_EXPERIENCE_MAX,
)


def _normalise_phone(value: str) -> str:
    """Parse to E.164. Rejects syntactically valid but unassigned numbers."""
    try:
        parsed = phonenumbers.parse(value, None)
    except phonenumbers.NumberParseException as exc:
        raise ValueError("Phone number must include a country code, e.g. +91 98765 43210") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise ValueError("Not a valid phone number for its country code")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def _normalise_technology(value: str) -> str:
    collapsed = " ".join(value.split())
    if not collapsed:
        raise ValueError("Technology name cannot be blank")
    return collapsed


def _reject_blank(value: str) -> str:
    collapsed = " ".join(value.split())
    if not collapsed:
        raise ValueError("Cannot be blank")
    return collapsed


def _require_real_tld(value: str) -> str:
    # EmailStr accepts a single-character TLD ("a@b.c"), which no real address has.
    tld = value.rsplit(".", 1)[-1]
    if len(tld) < 2:
        raise ValueError("Email domain is missing a valid top-level domain")
    return value.lower()


Email = Annotated[
    EmailStr,
    AfterValidator(_require_real_tld),
    Field(description="Candidate email address"),
]

PhoneNumber = Annotated[str, AfterValidator(_normalise_phone)]

FullName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=120),
    AfterValidator(_reject_blank),
]

Location = Annotated[
    str,
    StringConstraints(min_length=1, max_length=120),
    AfterValidator(_reject_blank),
]

DesiredPosition = Annotated[
    str,
    StringConstraints(min_length=1, max_length=120),
    AfterValidator(_reject_blank),
]

YearsOfExperience = Annotated[float, Field(ge=0, le=YEARS_OF_EXPERIENCE_MAX)]

TechnologyName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=TECHNOLOGY_NAME_MAX_LENGTH),
    AfterValidator(_normalise_technology),
]

AnswerText = Annotated[
    str,
    StringConstraints(min_length=ANSWER_MIN_LENGTH, max_length=ANSWER_MAX_LENGTH),
]


def deduplicate_technologies(values: list[Any]) -> list[Any]:
    """Case-insensitive dedupe that preserves the candidate's original ordering."""
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = str(value).casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    if len(result) > TECH_STACK_MAX_SIZE:
        raise ValueError(f"At most {TECH_STACK_MAX_SIZE} technologies may be declared")
    return result
