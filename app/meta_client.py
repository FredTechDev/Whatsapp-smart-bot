import io
import logging
import requests
from app.config import settings

logger = logging.getLogger(__name__)

class MetaProvider:
    """Send WhatsApp messages via Meta (WhatsApp Business Cloud API).
    Requires META_PHONE_NUMBER_ID and META_TOKEN in env.
    """
    def __init__(self):
        self.token = getattr(settings, "META_TOKEN", "")
        self.phone_number_id = getattr(settings, "META_PHONE_NUMBER_ID", "")
        self.base_url = f"https://graph.facebook.com/v15.0/{self.phone_number_id}/messages"
        self.app_secret = getattr(settings, "META_APP_SECRET", "")
        self.media_url = f"https://graph.facebook.com/v15.0/{self.phone_number_id}/media"

    def send(self, to: str, body: str):
        if not (self.token and self.phone_number_id):
            raise RuntimeError("META_TOKEN or META_PHONE_NUMBER_ID not configured")
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to.replace("whatsapp:", ""),
            "type": "text",
            "text": {"body": body}
        }
        r = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def upload_media(self, content_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """
        Upload media to Meta and return media_id. Uses the /{phone_number_id}/media endpoint.
        """
        if not (self.token and self.phone_number_id):
            raise RuntimeError("META_TOKEN or META_PHONE_NUMBER_ID not configured")
        files = {
            'file': ('voice.ogg', io.BytesIO(content_bytes), mime_type)
        }
        params = {"messaging_product": "whatsapp", "type": "audio"}
        headers = {"Authorization": f"Bearer {self.token}"}
        r = requests.post(self.media_url, headers=headers, files=files, data=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        # response contains 'id' key for the uploaded media
        return data.get('id')

    def validate_request(self, full_url: str, params, headers: dict, raw_body: bytes = None) -> bool:
        sig_header = headers.get("X-Hub-Signature-256") or headers.get("x-hub-signature-256")
        if not sig_header:
            logger.warning("Missing X-Hub-Signature-256 header")
            return False
        if not self.app_secret:
            logger.warning("META_APP_SECRET not configured; rejecting request")
            return False
        if raw_body is None:
            logger.warning("No raw body provided for Meta signature validation")
            return False
        try:
            prefix, signature = sig_header.split("=", 1)
        except Exception:
            logger.warning("Bad X-Hub-Signature-256 header format")
            return False
        if prefix.lower() != "sha256":
            logger.warning("Unsupported signature algorithm: %s", prefix)
            return False
        import hmac, hashlib
        mac = hmac.new(self.app_secret.encode(), msg=raw_body, digestmod=hashlib.sha256)
        expected = mac.hexdigest()
        import hmac as _h
        return _h.compare_digest(expected, signature)
