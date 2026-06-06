import requests
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def synthesize_eleven(text: str, voice: str = "alloy") -> tuple[bytes, str]:
    """Synthesize text to speech using ElevenLabs (blocking HTTP call). Returns (bytes, mime_type).
    """
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not configured")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    data = {"text": text, "voice_settings": {"stability": 0.6, "similarity_boost": 0.75}}
    r = requests.post(url, json=data, headers=headers, stream=True, timeout=30)
    r.raise_for_status()
    return r.content, r.headers.get("Content-Type", "audio/mpeg")
