"""LLM call wrapper.

Uses the OpenAI Python SDK against a configurable base URL, so it works with:
- OpenAI (fine-tuned models included)
- Groq, Together, Fireworks, DeepInfra, Anyscale
- Local vLLM / Ollama (with the openai-compatible endpoint)

If you use a provider whose SDK is not OpenAI-compatible (Anthropic, Cohere,
Vertex), replace the body of ``generate_answer`` — keep the signature stable.
"""

from __future__ import annotations

import logging
import re
import time
from typing import List

from openai import BadRequestError, OpenAI, RateLimitError

from app.config import settings
from app.rag.prompts import SYSTEM_PROMPT, ANSWER_TEMPLATE, build_context_block

log = logging.getLogger("gloria.generator")


_clients: dict[tuple[str, str], OpenAI] = {}

# Providers that hit a rate limit are skipped until this monotonic time.
_cooldown_until: dict[str, float] = {}
_DEFAULT_COOLDOWN_S = 60.0
_RETRY_DELAY_RX = re.compile(r"retryDelay'?\"?:\s*'?\"?(\d+(?:\.\d+)?)s")

# Which provider produced the most recent answer ("primary", "fallback", ...).
# Read by scripts.run_eval to show where each answer came from.
last_provider: str = ""


def _get_client(base_url: str, api_key: str) -> OpenAI:
    # Keyed by URL *and* key: two accounts on the same provider need two clients.
    key = (base_url, api_key)
    if key not in _clients:
        _clients[key] = OpenAI(base_url=base_url, api_key=api_key or "not-set")
    return _clients[key]


def _providers() -> list[tuple[str, str, str, str]]:
    """(label, base_url, api_key, model) in the order they should be tried."""
    providers = [("primary", settings.GLORIA_MODEL_BASE_URL,
                  settings.GLORIA_MODEL_API_KEY, settings.GLORIA_MODEL_NAME)]
    if settings.GLORIA_FALLBACK_API_KEY:
        providers.append(("fallback", settings.GLORIA_FALLBACK_BASE_URL,
                          settings.GLORIA_FALLBACK_API_KEY, settings.GLORIA_FALLBACK_MODEL_NAME))
    if settings.GLORIA_FALLBACK2_API_KEY:
        providers.append(("fallback2", settings.GLORIA_FALLBACK2_BASE_URL,
                          settings.GLORIA_FALLBACK2_API_KEY, settings.GLORIA_FALLBACK2_MODEL_NAME))
    return providers


def seconds_until_available() -> float:
    """0 if some provider can be called now, else seconds until the first one can."""
    now = time.monotonic()
    waits = [max(0.0, _cooldown_until.get(label, 0.0) - now) for label, *_ in _providers()]
    return min(waits, default=0.0)


def _cooldown_seconds(error: RateLimitError) -> float:
    """Use the provider's suggested retry delay when it gives one."""
    m = _RETRY_DELAY_RX.search(str(error))
    return float(m.group(1)) if m else _DEFAULT_COOLDOWN_S


def _reasoning_effort(model: str) -> str | None:
    """Reasoning ("thinking") models spend part of max_tokens on hidden
    reasoning before the visible answer; with a small budget the answer is
    cut off mid-sentence. Gloria's answers are short lookups from supplied
    context, so keep reasoning minimal. Returns None for models that don't
    accept the parameter (sending it to them is an error)."""
    if settings.GLORIA_REASONING_EFFORT:
        override = settings.GLORIA_REASONING_EFFORT.strip().lower()
        return None if override == "off" else override
    m = model.lower()
    if "gemini-2.5-flash" in m:
        return "none"          # Flash / Flash-Lite can switch thinking off
    if "gemini" in m or "gpt-oss" in m or m.startswith(("o1", "o3", "o4")):
        return "low"
    return None


def _complete(client: OpenAI, model: str, user_msg: str, max_tokens: int):
    kwargs = {}
    effort = _reasoning_effort(model)
    if effort:
        # extra_body: the pinned SDK predates the named parameter.
        kwargs["extra_body"] = {"reasoning_effort": effort}
    request = dict(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=settings.GLORIA_TEMPERATURE,
        max_tokens=max_tokens,
    )
    try:
        return client.chat.completions.create(**request, **kwargs)
    except BadRequestError as e:
        if not kwargs:
            raise
        # The provider doesn't accept reasoning_effort for this model.
        log.warning("%s rejected reasoning_effort (%s); retrying without it", model, e)
        return client.chat.completions.create(**request)


def generate_answer(question: str, hits: List[dict]) -> str:
    """Call the configured LLM and return Gloria's answer as plain text.

    Providers are tried in order. One that fails moves on to the next; one
    that is rate-limited is also skipped on later calls until its cooldown
    ends, so an exhausted daily quota doesn't cost a wasted request each time.
    An answer cut off by the token limit is retried once with double the
    budget on the same provider.
    """
    global last_provider
    context = build_context_block(hits)
    user_msg = ANSWER_TEMPLATE.format(question=question, context=context)

    last_error: Exception | None = None
    for label, base_url, api_key, model in _providers():
        if time.monotonic() < _cooldown_until.get(label, 0.0):
            continue
        client = _get_client(base_url, api_key)
        try:
            resp = _complete(client, model, user_msg, settings.GLORIA_MAX_TOKENS)
            if resp.choices[0].finish_reason == "length":
                log.warning("%s answer hit the token limit; retrying with a larger budget", label)
                resp = _complete(client, model, user_msg, settings.GLORIA_MAX_TOKENS * 2)
        except RateLimitError as e:
            wait = _cooldown_seconds(e)
            _cooldown_until[label] = time.monotonic() + wait
            log.warning("%s LLM rate-limited; skipping it for %.0fs", label, wait)
            last_error = e
            continue
        except Exception as e:  # noqa: BLE001
            log.warning("%s LLM failed: %s", label, e)
            last_error = e
            continue
        answer = (resp.choices[0].message.content or "").strip()
        if not answer:
            log.warning("%s returned an empty answer (finish_reason=%s)", label,
                        resp.choices[0].finish_reason)
            last_error = RuntimeError(f"{label} returned an empty answer")
            continue
        last_provider = label
        return answer
    raise last_error or RuntimeError("all LLM providers are rate-limited; try later")
