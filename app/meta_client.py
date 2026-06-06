import hmac
import hashlib
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

    def validate_request(self, full_url: str, params, headers: dict, raw_body: bytes = None) -> bool:
        """
        Validate Meta (Facebook) webhook signature. Must compute HMAC-SHA256 over raw request body bytes
        and compare to X-Hub-Signature-256 header which is of the form: sha256=<hex>

        Args:
            full_url: not used for Meta but kept for interface compatibility
            params: parsed params/payload (not used for signature check)
            headers: request headers mapping
            raw_body: raw request body bytes (required)
        Returns:
            bool indicating whether signature is valid
        """
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
        mac = hmac.new(self.app_secret.encode(), msg=raw_body, digestmod=hashlib.sha256)
        expected = mac.hexdigest()
        return hmac.compare_digest(expected, signature)
