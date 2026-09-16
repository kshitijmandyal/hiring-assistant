"""Thresholds for the grading guardrails.

Candidates have a direct incentive to manipulate their own grade, so text they supply
is treated as hostile input rather than as trusted prompt content.
"""

import re
from typing import Final

UNTRUSTED_TAG: Final = "candidate_answer"

# Two criteria worded slightly differently should still match; two different criteria
# should not. 0.85 separates rewording from substitution on the rubric strings we emit.
CRITERION_MATCH_THRESHOLD: Final = 0.85

# Headroom over what the met-criteria ratio strictly supports, so ordinary grader
# judgement is not clamped — only scores the rubric cannot justify at all.
SCORE_COHERENCE_ALLOWANCE: Final = 2

# If the grader met no criteria whatsoever, no score above this is defensible.
UNMET_SCORE_CEILING: Final = 2

# Telemetry only — never used to reject an answer, since a candidate can legitimately
# discuss prompt injection when the question is about LLM security.
INJECTION_MARKERS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"ignore\s+(?:all\s+|any\s+)?(?:previous|prior|above)\s+instruction", re.I),
    re.compile(r"disregard\s+(?:the\s+)?(?:rubric|instruction|above)", re.I),
    re.compile(r"</?\s*candidate_answer", re.I),
    re.compile(r"^\s*(?:system|assistant)\s*:", re.I | re.M),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\b", re.I),
    re.compile(r"\bscore\s*[:=]\s*(?:10|ten)\b", re.I),
    re.compile(r"award\s+(?:full|maximum|max)\s+(?:marks|score|points)", re.I),
)

# Everything except tab and newline; these can be used to smuggle formatting past review.
CONTROL_CHARACTERS: Final = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
