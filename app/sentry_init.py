import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry if SENTRY_DSN is configured. Safe to call multiple times."""
    dsn = getattr(settings, "SENTRY_DSN", "")
    if not dsn:
        logger.debug("SENTRY_DSN not set; skipping Sentry init")
        return
    try:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1, integrations=[StarletteIntegration()])
        logger.info("Sentry initialized")
    except Exception:
        logger.exception("Failed to initialize Sentry")
