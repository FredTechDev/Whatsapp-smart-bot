import io
import asyncio
import logging
import subprocess
import tempfile
from app.config import settings
import openai

logger = logging.getLogger(__name__)
openai.api_key = settings.OPENAI_API_KEY

async def transcribe_audio_openai(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """Transcribe audio bytes using OpenAI Whisper (synchronous SDK called in thread).
    Returns the transcript string.
    """
    loop = asyncio.get_event_loop()
    def _call():
        f = io.BytesIO(audio_bytes)
        # Depending on SDK version: use openai.Audio.transcribe or openai.Whisper
        try:
            resp = openai.Audio.transcribe("whisper-1", f)
            # newer SDKs return object with 'text'
            if isinstance(resp, dict):
                return resp.get('text', '')
            return getattr(resp, 'text', '')
        except Exception:
            # fallback: try ChatCompletion with base64? Not implemented
            raise
    return await loop.run_in_executor(None, _call)


def _convert_to_ogg_opus(input_bytes: bytes) -> bytes:
    """Use ffmpeg (must be installed) to convert input bytes to opus-in-ogg bytes.
    Fall back to returning original bytes on failure.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".in", delete=True) as inf, tempfile.NamedTemporaryFile(suffix=".ogg", delete=True) as outf:
            inf.write(input_bytes)
            inf.flush()
            cmd = [
                'ffmpeg', '-y', '-i', inf.name,
                '-c:a', 'libopus', '-b:a', '32k', '-vbr', 'on', '-application', 'voip',
                '-f', 'ogg', outf.name
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            outf.flush()
            outf.seek(0)
            return outf.read()
    except Exception:
        logger.exception("ffmpeg conversion failed; returning input bytes")
        return input_bytes

async def convert_to_ogg_opus_async(input_bytes: bytes) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _convert_to_ogg_opus, input_bytes)
