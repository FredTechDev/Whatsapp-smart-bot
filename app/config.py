from pydantic import BaseSettings

class Settings(BaseSettings):
    TWILIO_SID: str = ""
    TWILIO_AUTH: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    PORT: int = 8000
    WEBHOOK_SECRET_TOKEN: str = ""

    # ML & model settings
    CLASSIFIER_MODE: str = "rule"  # 'rule' or 'ml'
    MODEL_PATH: str = "models/urgency_model.joblib"

    # Messaging provider
    WHATSAPP_PROVIDER: str = "twilio"

    # Meta settings (optional)
    META_TOKEN: str = ""
    META_PHONE_NUMBER_ID: str = ""
    META_APP_SECRET: str = ""
    META_VERIFY_TOKEN: str = ""

    # Public webhook URL override (useful when behind proxy / ngrok)
    WEBHOOK_PUBLIC_URL: str = ""

    # LLM / OpenAI settings
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_RATE_LIMIT_RPS: float = 1.0
    LLM_MAX_HISTORY_MESSAGES: int = 8
    LLM_TIMEOUT_SECONDS: int = 10
    LLM_MAX_TOKENS: int = 200

    # Observability / Sentry
    SENTRY_DSN: str = ""

    # Voice settings
    STT_PROVIDER: str = "openai"  # openai|assemblyai|gcp|aws
    TTS_PROVIDER: str = "elevenlabs"  # elevenlabs|gcp|aws|openai
    ELEVENLABS_API_KEY: str = ""

    # S3 (for hosting media for Twilio). If not set, Twilio uploads may fail.
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Allowed media types
    ALLOWED_MEDIA_TYPES: str = "audio/ogg,audio/opus,audio/mpeg,audio/mp3"

    class Config:
        env_file = ".env"

settings = Settings()
