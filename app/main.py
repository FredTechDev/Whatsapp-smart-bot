from fastapi import FastAPI, Request, HTTPException
import logging
from app.classifier import classify_urgency
from app.convo_store import ConvoStore
from app.reply_generator import generate_reply
from app.messaging import client as messaging_client
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
store = ConvoStore(redis_url=settings.REDIS_URL)

@app.get("/webhook")
async def webhook_verify(request: Request):
    # Used for Meta/WhatsApp webhook verification
    params = dict(request.query_params)
    mode = params.get("hub.mode") or params.get("mode")
    challenge = params.get("hub.challenge") or params.get("challenge")
    verify_token = params.get("hub.verify_token") or params.get("verify_token")
    expected = getattr(settings, "META_VERIFY_TOKEN", "")
    if mode == "subscribe" and verify_token == expected:
        return int(challenge or 0)
    raise HTTPException(status_code=400, detail="Invalid verify token")

@app.post("/webhook")
async def webhook(request: Request):
    # Twilio posts form-encoded data; Meta posts JSON
    headers = {k: v for k, v in request.headers.items()}

    # read raw body for signature checks
    raw = await request.body()

    # determine public URL to validate Twilio signatures when behind a proxy
    public_url = settings.WEBHOOK_PUBLIC_URL or str(request.url)

    # parse depending on provider
    provider = getattr(settings, "WHATSAPP_PROVIDER", "twilio").lower()

    if provider == "meta":
        try:
            payload = await request.json()
        except Exception:
            logger.exception("Failed to parse JSON payload from Meta")
            raise HTTPException(status_code=400, detail="Malformed JSON payload")
        params = payload
        # Validate request via messaging client (pass raw body)
        valid = messaging_client.validate_request(public_url, params, headers, raw)
        if not valid:
            logger.warning("Invalid Meta webhook signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
        # extract message content (WhatsApp Cloud API structure)
        try:
            entry = payload.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return {"status": "no_message"}
            message = messages[0]
            body = message.get("text", {}).get("body", "")
            from_number = "whatsapp:" + message.get("from", "")
        except Exception as e:
            logger.exception("Failed to parse Meta payload")
            raise HTTPException(status_code=400, detail="Malformed payload")
    else:
        # Twilio
        form = await request.form()
        body = form.get("Body") or ""
        from_number = form.get("From") or ""
        params = dict(form)
        # Validate request
        valid = messaging_client.validate_request(public_url, params, headers)
        if not valid:
            logger.warning("Invalid Twilio signature")
            raise HTTPException(status_code=403, detail="Invalid signature")

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
        history = await store.get_history(from_number, limit=10)
        reply = await generate_reply(body, history)
    # Send reply via provider client
    try:
        messaging_client.send(to=from_number, body=reply)
    except Exception:
        logger.exception("Failed to send message")
        raise HTTPException(status_code=500, detail="Failed to send message")

    return {"status": "ok", "urgency": urgency}
