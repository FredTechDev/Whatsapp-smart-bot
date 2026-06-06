import os
import openai
import asyncio
import logging
from typing import List
from app.config import settings
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

try:
    from aiolimiter import AsyncLimiter
except Exception:
    AsyncLimiter = None

logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are a concise, empathetic assistant that helps users over WhatsApp. "
    "When appropriate, ask clarifying questions. When a message appears urgent, suggest escalation. "
    "Keep replies short (1-3 sentences) and actionable."
)

# Rate limiter (simple per-process limiter). If aiolimiter isn't installed, we'll fall back to no rate-limiting.
_limiter = AsyncLimiter(max_rate=settings.LLM_RATE_LIMIT_RPS, time_period=1) if AsyncLimiter else None


@retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def _call_openai_sync(messages, model="gpt-3.5-turbo"):
    # Synchronous call to OpenAI ChatCompletion (run in thread) -- wrapped with retries
    resp = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=settings.LLM_MAX_TOKENS, temperature=0.3)
    # Compatibility: some SDKs return choices with message.content; adjust as needed
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        # fallback for older SDK response shape
        return resp.choices[0].text.strip()


async def generate_reply(incoming_text: str, history: List[dict]):
    # Short-circuit if no OpenAI key
    if not settings.OPENAI_API_KEY:
        logger.info("OPENAI_API_KEY not set; using fallback reply")
        return "Thanks — I received your message. Can you tell me more?"

    # Cap history length
    if history and len(history) > settings.LLM_MAX_HISTORY_MESSAGES:
        history = history[-settings.LLM_MAX_HISTORY_MESSAGES:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for item in history:
            text = item.get("text", "")
            messages.append({"role": "user", "content": text})

    messages.append({"role": "user", "content": incoming_text})

    # Acquire rate limiter token if available
    try:
        if _limiter:
            await _limiter.acquire()
        # run blocking OpenAI call in a thread with timeout
        loop = asyncio.get_event_loop()
        try:
            raw = await asyncio.wait_for(loop.run_in_executor(None, _call_openai_sync, messages, settings.LLM_MODEL), timeout=settings.LLM_TIMEOUT_SECONDS)
            return raw
        except asyncio.TimeoutError:
            logger.exception("OpenAI call timed out")
            return "Thanks — I received your message. Can you tell me more?"
    except Exception:
        logger.exception("LLM generation failed")
        return "Thanks — I received your message. Can you tell me more?"
    finally:
        # No explicit release needed for aiolimiter
        pass
