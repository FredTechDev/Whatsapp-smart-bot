import json
import hmac
import hashlib
from app.meta_client import MetaProvider
from app.twilio_client import TwilioProvider
from app.config import settings


# This file contains a few sample headers and payloads used for unit testing signature validation.

def make_meta_signature(secret: str, body_bytes: bytes) -> str:
    mac = hmac.new(secret.encode(), msg=body_bytes, digestmod=hashlib.sha256)
    return "sha256=" + mac.hexdigest()


def make_twilio_signature(auth_token: str, url: str, params: dict) -> str:
    # Twilio RequestValidator can compute this but in unit tests we'll use the validator directly
    from twilio.request_validator import RequestValidator
    rv = RequestValidator(auth_token)
    return rv.compute_signature(url, params)


def test_meta_signature_validation():
    secret = "test_app_secret"
    payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "14155551234", "text": {"body": "hello"}}]}}]}]}
    body = json.dumps(payload).encode()
    header = make_meta_signature(secret, body)
    provider = MetaProvider()
    # inject secret for test
    provider.app_secret = secret
    headers = {"X-Hub-Signature-256": header}
    assert provider.validate_request("", payload, headers, raw_body=body) is True


def test_twilio_signature_validation():
    auth = "test_auth_token"
    url = "https://example.com/webhook"
    params = {"Body": "hello", "From": "whatsapp:+14155551234"}
    provider = TwilioProvider()
    provider.validator = None
    # create a validator for testing
    from twilio.request_validator import RequestValidator
    provider.validator = RequestValidator(auth)
    sig = provider.validator.compute_signature(url, params)
    headers = {"X-Twilio-Signature": sig}
    assert provider.validate_request(url, params, headers) is True
