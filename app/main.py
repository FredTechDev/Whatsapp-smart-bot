from fastapi import FastAPI, Request, HTTPException
import os
from app.classifier import classify_urgency
from app.convo_store import ConvoStore
from app.reply_generator import generate_reply
from app.twilio_client import send_whatsapp_message
from app.config import settings

app = FastAPI()
store = ConvoStore(redis_url=settings.REDIS_URL)

@app.post("/webhook")
async def webhook(request: Request):
    # Twilio posts form-encoded data for incoming messages
    form = await request.form()
    body = form.get("Body") or ""
    from_number = form.get("From") or ""
    if not from_number:
        raise HTTPException(status_code=400, detail="Missing From")
    # Classify urgency
    urgency, score = classify_urgency(body)
    # Persist message and metadata
    await store.append_message(from_number, {"text": body, "urgency": urgency, "score": score})
    # Decide response
    if urgency == "high":
        reply = "I detected this might be urgent. Do you want me to escalate this to support now?"
    else:
        # Use LLM or template to generate contextual reply
        history = await store.get_history(from_number, limit=10)
        reply = await generate_reply(body, history)
    # Send reply via Twilio
    send_whatsapp_message(to=from_number, body=reply)
    return {"status": "ok", "urgency": urgency}
