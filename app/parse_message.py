from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def _parse_twilio(form: Dict[str, Any]) -> Dict[str, Any]:
    # Twilio sends form-encoded fields. Media fields are MediaUrl0..N and NumMedia
    num_media = int(form.get("NumMedia") or 0)
    media: List[Dict[str, str]] = []
    for i in range(num_media):
        url_key = f"MediaUrl{i}"
        content_type_key = f"MediaContentType{i}"
        url = form.get(url_key)
        ctype = form.get(content_type_key)
        if url:
            media.append({"url": url, "content_type": ctype or ""})

    message_id = form.get("MessageSid") or form.get("SmsSid")
    from_number = form.get("From") or form.get("FromCountry")
    text = form.get("Body") or ""

    # Twilio interactive/template messages may come through other fields; include full raw form
    return {
        "provider": "twilio",
        "message_id": message_id,
        "from": from_number,
        "type": "media" if media else "text",
        "text": text,
        "media": media,
        "interactive": None,
        "raw": dict(form)
    }


def _parse_meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Meta / WhatsApp Cloud sends nested JSON. We defensively parse common message types.
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
    except Exception:
        value = payload

    messages = value.get("messages") or []
    if not messages:
        return {
            "provider": "meta",
            "message_id": None,
            "from": None,
            "type": "unknown",
            "text": "",
            "media": [],
            "interactive": None,
            "raw": payload
        }

    message = messages[0]
    msg_id = message.get("id") or message.get("message_id")
    from_num = message.get("from")

    # Text message
    text = ""
    if "text" in message and isinstance(message.get("text"), dict):
        text = message.get("text", {}).get("body", "")

    # Media handling (image, audio, document, video)
    media = []
    for mtype in ("image", "audio", "video", "document", "sticker", "location"):
        if mtype in message:
            m = message.get(mtype, {})
            # Meta often provides an id which must be fetched via media API; include available fields
            media.append({"type": mtype, "id": m.get("id"), "mime_type": m.get("mime_type")})

    # Interactive messages (buttons, list replies)
    interactive = None
    if "interactive" in message:
        interactive = message.get("interactive")

    # Template messages may appear in 'template' key
    if "template" in message:
        interactive = interactive or {}
        interactive.update({"template": message.get("template")})

    return {
        "provider": "meta",
        "message_id": msg_id,
        "from": f"whatsapp:{from_num}" if from_num else None,
        "type": "media" if media else ("interactive" if interactive else "text"),
        "text": text,
        "media": media,
        "interactive": interactive,
        "raw": payload
    }


def normalize_message(provider: str, payload: Any) -> Dict[str, Any]:
    """Normalize provider-specific payloads into a common internal message shape.

    Returns dict with keys: provider, message_id, from, type, text, media, interactive, raw
    """
    provider = (provider or "").lower()
    try:
        if provider == "meta":
            return _parse_meta(payload or {})
        else:
            # treat anything else as Twilio-style form
            return _parse_twilio(payload or {})
    except Exception as e:
        logger.exception("Failed to normalize message for provider=%s", provider)
        return {
            "provider": provider,
            "message_id": None,
            "from": None,
            "type": "unknown",
            "text": "",
            "media": [],
            "interactive": None,
            "raw": payload
        }
