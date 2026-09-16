"""Logging setup with redaction.

Candidate data must never reach a log line, so redaction happens in a filter rather
than at each call site — a filter cannot be forgotten, a convention can.
"""

import logging
import re
import uuid
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger.json import JsonFormatter

from talentscout.constants import CORRELATION_ID_LENGTH, SENSITIVE_FIELDS

REDACTED = "[redacted]"

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")

# Belt-and-braces for PII interpolated into a message string rather than passed as an extra.
# Quantifiers are bounded rather than open-ended: these run against every log line,
# and an unbounded class can backtrack super-linearly on adversarial input.
_EMAIL_PATTERN = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,4}")
_PHONE_PATTERN = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,18}\d(?!\w)")
_UUID_PATTERN = re.compile(
    r"(?<!\w)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?!\w)",
    re.IGNORECASE,
)


def new_correlation_id() -> str:
    return uuid.uuid4().hex[:CORRELATION_ID_LENGTH]


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> str:
    return _correlation_id.get()


# LogRecord's own attributes collide with our field names ("name" is the logger's name,
# not a person's), so only genuine extras are eligible for redaction.
_RESERVED_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "correlation_id",
    "taskName",
}


class RedactingFilter(logging.Filter):
    """Strips sensitive extras and scrubs PII patterns out of the rendered message."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key in record.__dict__:
            if key in _RESERVED_RECORD_ATTRS:
                continue
            if key.lower() in SENSITIVE_FIELDS:
                record.__dict__[key] = REDACTED

        if isinstance(record.msg, str):
            record.msg = self._scrub(record.msg)
        if record.args:
            record.args = self._scrub_args(record.args)

        return True

    @staticmethod
    def _scrub(text: str) -> str:
        text = _EMAIL_PATTERN.sub(REDACTED, text)
        text = _PHONE_PATTERN.sub(REDACTED, text)
        return _UUID_PATTERN.sub(REDACTED, text)

    def _scrub_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._scrub(value)
        # UUIDs reach here as objects via "%s" and would otherwise bypass the patterns.
        if isinstance(value, uuid.UUID):
            return REDACTED
        return value

    def _scrub_args(self, args: Any) -> Any:
        if isinstance(args, dict):
            return {k: self._scrub_value(v) for k, v in args.items()}
        if isinstance(args, tuple):
            return tuple(self._scrub_value(a) for a in args)
        return args


class CorrelationIdFilter(logging.Filter):
    """Attaches the request's correlation id, which replaces IDs as the way to trace a flow."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True


def configure_logging(*, level: str = "INFO", json_output: bool = False) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    handler.addFilter(CorrelationIdFilter())

    if json_output:
        handler.setFormatter(
            JsonFormatter(
                "{asctime}{levelname}{name}{message}{correlation_id}",
                style="{",
                rename_fields={"asctime": "timestamp", "levelname": "level"},
            )
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s [%(correlation_id)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Access logs would duplicate our own request logging, without the redaction filter.
    logging.getLogger("uvicorn.access").disabled = True

    # The Anthropic SDK is built on httpx2, which logs every request at INFO.
    for noisy in ("httpx", "httpx2", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
