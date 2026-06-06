from langdetect import detect, DetectorFactory
import logging

DetectorFactory.seed = 0
logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """Detect language code (ISO 639-1) for a given text.

    Returns language code (e.g., 'en', 'fr', 'sw') or 'en' on failure.
    """
    if not text or not isinstance(text, str):
        return 'en'
    try:
        lang = detect(text)
        return lang
    except Exception:
        logger.exception('Language detection failed, defaulting to en')
        return 'en'
