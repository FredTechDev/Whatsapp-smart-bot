import os
import openai
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from app.config import settings

openai.api_key = settings.OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are a concise, empathetic assistant that helps users over WhatsApp. "
    "When appropriate, ask clarifying questions. When a message appears urgent, suggest escalation. "
    "Keep replies short (1-3 sentences) and actionable."
)


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def _call_openai_sync(messages, model="gpt-3.5-turbo"):
    resp = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=200, temperature=0.3)
    return resp.choices[0].message.content.strip()


async def generate_reply(incoming_text: str, history):
    # If OPENAI_API_KEY not set, return fallback
    if not settings.OPENAI_API_KEY:
        return "Thanks — I received your message. Can you tell me more?"

    # If history is long, compress/summarize the earlier part (simple approach: keep last 8 messages)
    recent = history[-8:] if history and len(history) > 8 else history

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Add history as user messages
    if recent:
        for item in recent:
            text = item.get("text", "")
            messages.append({"role": "user", "content": text})

    messages.append({"role": "user", "content": incoming_text})

    # Call OpenAI synchronously inside thread to keep compatibility with sync SDK
    loop = asyncio.get_event_loop()
    try:
        reply = await loop.run_in_executor(None, _call_openai_sync, messages)
        return reply
    except Exception:
        return "Thanks — I received your message. Can you tell me more?"
