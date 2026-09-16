"""Thin wrapper over the Anthropic SDK.

Owns three things the rest of the adapter should not repeat: prompt loading,
translation of SDK exceptions into our own, and the structured-output call itself.
"""

import logging
from functools import cache
from pathlib import Path
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from talentscout.constants import PromptId
from talentscout.exceptions import LLMRateLimitedError, LLMUnavailableError

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"

ResponseT = TypeVar("ResponseT", bound=BaseModel)


@cache
def load_prompt(prompt_id: PromptId) -> str:
    """Read a system prompt from disk. Cached — prompts are immutable at runtime."""
    path = _PROMPTS_DIR / f"{prompt_id.value}.md"
    if not path.is_file():
        raise LLMUnavailableError(f"Prompt template '{prompt_id.value}' is missing")
    return path.read_text(encoding="utf-8").strip()


class ClaudeClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_tokens: int,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def parse(
        self,
        *,
        prompt_id: PromptId,
        user_content: str,
        output_format: type[ResponseT],
    ) -> ResponseT:
        """One constrained-decoding call. The schema is enforced server-side, so the
        result needs no parsing — the previous implementation regex-scraped a numbered list.
        """
        try:
            response = await self._client.messages.parse(
                model=self._model,
                max_tokens=self._max_tokens,
                thinking={"type": "adaptive"},
                system=[
                    {
                        "type": "text",
                        "text": load_prompt(prompt_id),
                        # Stable prefix, so repeated calls in one interview read from cache.
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_content}],
                output_format=output_format,
            )
        except anthropic.RateLimitError as exc:
            retry_after = exc.response.headers.get("retry-after")
            raise LLMRateLimitedError(
                "Claude is rate limiting requests",
                retry_after_seconds=int(retry_after) if retry_after else None,
            ) from exc
        except anthropic.AuthenticationError as exc:
            raise LLMUnavailableError("Anthropic API key is missing or invalid") from exc
        except anthropic.APIStatusError as exc:
            raise LLMUnavailableError(f"Claude returned {exc.status_code}") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMUnavailableError("Could not reach the Anthropic API") from exc

        if response.stop_reason == "refusal":
            raise LLMUnavailableError("Claude declined to respond to this request")

        parsed = response.parsed_output
        if parsed is None:
            raise LLMUnavailableError("Claude returned no structured output")

        logger.debug(
            "Claude call complete: prompt=%s in=%d out=%d cached=%d",
            prompt_id.value,
            response.usage.input_tokens,
            response.usage.output_tokens,
            response.usage.cache_read_input_tokens or 0,
        )
        return parsed

    async def aclose(self) -> None:
        await self._client.close()


def build_client(*, api_key: str, model: str, max_tokens: int) -> ClaudeClient:
    return ClaudeClient(api_key=api_key, model=model, max_tokens=max_tokens)


__all__ = ["ClaudeClient", "build_client", "load_prompt"]
