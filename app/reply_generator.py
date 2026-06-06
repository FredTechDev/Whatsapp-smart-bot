import asyncio
import logging
from typing import List
import openai
from app.config import settings

logger = logging.getLogger(__name__)
openai.api_key = settings.OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are a concise, empathetic assistant that helps users over WhatsApp. "
    "When appropriate, ask clarifying questions. When a message appears urgent, suggest escalation. "
    "Keep replies short (1-3 sentences) and actionable."
)


def _call_openai_sync(messages, model="gpt-3.5-turbo"):
    resp = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=settings.LLM_MAX_TOKENS, temperature=0.3)
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        return resp.choices[0].text.strip()


async def generate_reply(incoming_text: str, history: List[dict], lang: str | None = None):
    # Short-circuit if no OpenAI key
    if not settings.OPENAI_API_KEY:
        logger.info("OPENAI_API_KEY not set; using fallback reply")
        return "Thanks — I received your message. Can you tell me more?"

    # Cap history length
    if history and len(history) > settings.LLM_MAX_HISTORY_MESSAGES:
        history = history[-settings.LLM_MAX_HISTORY_MESSAGES:]

    system = SYSTEM_PROMPT
    if lang:
        # ask LLM to reply in the detected language (give short instruction)
        system = system + f" Reply in the user's language: {lang}."

    messages = [{"role": "system", "content": system}]
    if history:
        for item in history:
            text = item.get("text", "")
            messages.append({"role": "user", "content": text})

    messages.append({"role": "user", "content": incoming_text})

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
