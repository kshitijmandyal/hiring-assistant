"""Input and output guardrails for grading.

The candidate writes the text we ask Claude to judge, and benefits from a high score,
so their answer is untrusted input. Three defences, in order of how much they can be
relied on:

1. Structural — the answer is delimited and the prompt says to treat it as data.
   Mitigates, never eliminates.
2. Deterministic verification — the criteria Claude scored must be the ones we sent.
   Cannot be talked out of, because no model output is involved in the check.
3. Coherence clamping — a score the graded criteria cannot support is reduced.

Defence 1 can be argued with; 2 and 3 cannot, which is why the score ultimately rests
on them rather than on prompt wording.
"""

import logging
import math
import unicodedata
from difflib import SequenceMatcher
from enum import StrEnum

from talentscout.adapters.claude.schemas import LLMCriterionScore
from talentscout.constants.guardrails import (
    CONTROL_CHARACTERS,
    CRITERION_MATCH_THRESHOLD,
    INJECTION_MARKERS,
    SCORE_COHERENCE_ALLOWANCE,
    UNMET_SCORE_CEILING,
    UNTRUSTED_TAG,
)
from talentscout.domain.assessment import MAX_QUESTION_SCORE

logger = logging.getLogger(__name__)


class GuardrailFlag(StrEnum):
    INJECTION_MARKERS_PRESENT = "injection_markers_present"
    INVENTED_CRITERIA = "invented_criteria"
    MISSING_CRITERIA = "missing_criteria"
    SCORE_CLAMPED = "score_clamped"
    NO_CRITERIA_RETURNED = "no_criteria_returned"


# --- Input ------------------------------------------------------------------


def sanitise_untrusted(text: str) -> str:
    """Neutralise the ways candidate text could escape its delimiter.

    Unicode is normalised first: without it, a fullwidth or combining-character variant
    of the closing tag would survive the literal replacement below.
    """
    # NFKC first, so fullwidth and compatibility forms (e.g. U+FF1C) collapse to plain
    # angle brackets and are caught by the escaping below rather than slipping past it.
    normalised = unicodedata.normalize("NFKC", text)
    stripped = CONTROL_CHARACTERS.sub("", normalised)
    return stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap_untrusted(text: str) -> str:
    return f"<{UNTRUSTED_TAG}>\n{sanitise_untrusted(text)}\n</{UNTRUSTED_TAG}>"


def detect_injection_markers(text: str) -> list[str]:
    """Telemetry only.

    Never rejects an answer: a candidate asked about LLM security may legitimately
    write "ignore previous instructions" as the subject of their answer.
    """
    return [p.pattern for p in INJECTION_MARKERS if p.search(text)]


# --- Output -----------------------------------------------------------------


def _normalise_criterion(text: str) -> str:
    return " ".join(text.casefold().split())


def _matches(expected: str, returned: str) -> bool:
    a, b = _normalise_criterion(expected), _normalise_criterion(returned)
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= CRITERION_MATCH_THRESHOLD


def check_rubric_fidelity(
    *,
    expected_criteria: list[str],
    returned: list[LLMCriterionScore],
) -> tuple[list[LLMCriterionScore], list[GuardrailFlag]]:
    """Keep only scores whose criterion was actually in the rubric we sent.

    An invented criterion is the clearest signal that the grader followed instructions
    from somewhere other than us.
    """
    flags: list[GuardrailFlag] = []
    kept: list[LLMCriterionScore] = []
    matched_expected: set[int] = set()

    for score in returned:
        match_index = next(
            (
                i
                for i, expected in enumerate(expected_criteria)
                if _matches(expected, score.criterion)
            ),
            None,
        )
        if match_index is None:
            continue
        matched_expected.add(match_index)
        kept.append(score)

    if len(kept) < len(returned):
        flags.append(GuardrailFlag.INVENTED_CRITERIA)
    if len(matched_expected) < len(expected_criteria):
        flags.append(GuardrailFlag.MISSING_CRITERIA)
    if not kept:
        flags.append(GuardrailFlag.NO_CRITERIA_RETURNED)

    return kept, flags


def supported_score_ceiling(*, met: int, total: int) -> int:
    """Highest score the met criteria can justify."""
    if total == 0 or met == 0:
        return UNMET_SCORE_CEILING
    ratio_ceiling = math.ceil(met / total * MAX_QUESTION_SCORE) + SCORE_COHERENCE_ALLOWANCE
    return min(ratio_ceiling, MAX_QUESTION_SCORE)


def check_score_coherence(
    *,
    score: int,
    criterion_scores: list[LLMCriterionScore],
    expected_total: int,
) -> tuple[int, list[GuardrailFlag]]:
    met = sum(1 for cs in criterion_scores if cs.met)
    ceiling = supported_score_ceiling(met=met, total=expected_total)
    if score > ceiling:
        return ceiling, [GuardrailFlag.SCORE_CLAMPED]
    return score, []


def log_guardrail_event(*, flags: list[GuardrailFlag], markers: list[str], technology: str) -> None:
    """Records that something tripped, without echoing the candidate's text."""
    if not flags and not markers:
        return
    logger.warning(
        "Grading guardrail tripped for %s: flags=%s injection_markers=%d",
        technology,
        ",".join(f.value for f in flags) or "none",
        len(markers),
    )
