import os
import openai
from app.config import settings

openai.api_key = settings.OPENAI_API_KEY

async def generate_reply(incoming_text: str, history):
    # If OPENAI_API_KEY is set, use ChatCompletion for contextual replies, otherwise fallback.
    if settings.OPENAI_API_KEY:
        # Build a simple conversation for the LLM from history
        messages = [
            {"role": "system", "content": "You are a helpful assistant that replies concisely and empathetically."}
        ]
        for item in history:
            # assume message dicts have 'text' and maybe 'sender' (not enforced here)
            messages.append({"role": "user", "content": item.get("text", "")})
        messages.append({"role": "user", "content": incoming_text})
        try:
            resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=200)
            return resp.choices[0].message.content.strip()
        except Exception:
            # fallback
            return "Thanks — I received your message. Can you tell me more?"
    else:
        return "Thanks — I received your message. Can you tell me more?"
