import logging
from app.config import settings
from app.twilio_client import TwilioProvider
from app.meta_client import MetaProvider

logger = logging.getLogger(__name__)

class MessagingClient:
    def __init__(self):
        provider = getattr(settings, "WHATSAPP_PROVIDER", "twilio").lower()
        if provider == "meta":
            self._client = MetaProvider()
        else:
            self._client = TwilioProvider()

    def send(self, to: str, body: str):
        return self._client.send(to=to, body=body)

    def validate_request(self, full_url: str, params, headers: dict, raw_body: bytes = None) -> bool:
        # Delegate to provider-specific validation. Meta requires raw_body for HMAC validation.
        if hasattr(self._client, "validate_request"):
            try:
                return self._client.validate_request(full_url, params, headers, raw_body)
            except TypeError:
                # Some providers expect (full_url, params, headers) without raw_body
                return self._client.validate_request(full_url, params, headers)
        return False

# singleton
client = MessagingClient()
