from twilio.rest import Client as TwilioClient
from twilio.request_validator import RequestValidator
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class TwilioProvider:
    def __init__(self):
        self.client = TwilioClient(settings.TWILIO_SID, settings.TWILIO_AUTH)
        self.validator = RequestValidator(settings.TWILIO_AUTH) if settings.TWILIO_AUTH else None

    def send(self, to: str, body: str):
        return self.client.messages.create(
            body=body,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=to
        )

    def validate_request(self, full_url: str, params: dict, headers: dict) -> bool:
        """
        Validate Twilio request using the RequestValidator. full_url must be the public-facing URL
        (including scheme) that Twilio calls. If the app is behind a proxy, set WEBHOOK_PUBLIC_URL in env
        to the public URL.
        """
        if not self.validator:
            logger.warning("Twilio validator not configured; rejecting request")
            return False
        signature = headers.get("X-Twilio-Signature") or headers.get("x-twilio-signature") or ""
        try:
            return self.validator.validate(full_url, params, signature)
        except Exception:
            logger.exception("Twilio signature validation failed")
            return False
