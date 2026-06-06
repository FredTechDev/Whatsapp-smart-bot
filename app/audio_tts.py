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


def synthesize_google_tts(text: str, lang: str = "en-US") -> tuple[bytes, str]:
    """Synthesize using Google Cloud Text-to-Speech if available.
    Returns (audio_bytes, mime_type) or raises if the library is not installed.
    """
    try:
        from google.cloud import texttospeech
    except Exception as e:
        raise RuntimeError("google-cloud-texttospeech not available") from e

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    # choose a standard voice for the requested language
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.OGG_OPUS)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    return response.audio_content, "audio/ogg"


def synthesize_preferred(text: str, lang: str = "en") -> tuple[bytes, str]:
    """Synthesize text to speech trying preferred providers based on language.
    Strategy:
      - Try ElevenLabs first (if configured)
      - If it fails and GOOGLE_TTS_ENABLED is true, try Google Cloud TTS with the language code
      - Otherwise raise and let the caller handle fallback
    Returns (audio_bytes, mime_type)
    """
    # Try ElevenLabs
    try:
        audio, mime = synthesize_eleven(text, voice="alloy")
        return audio, mime
    except Exception:
        logger.exception("ElevenLabs TTS failed or unavailable for language %s", lang)
    # Fallback to Google if enabled
    if getattr(settings, "GOOGLE_TTS_ENABLED", False):
        try:
            # Google expects a BCP-47 language tag like en-US. Try to map a 2-letter code to en-US style.
            lang_tag = lang if '-' in lang else (lang + '-US') if lang == 'en' else lang + '-'+lang.upper()
            audio, mime = synthesize_google_tts(text, lang_tag)
            return audio, mime
        except Exception:
            logger.exception("Google TTS fallback failed for lang=%s", lang)
    # If we reach here, no provider was available
    raise RuntimeError("No TTS provider available or synthesis failed")
