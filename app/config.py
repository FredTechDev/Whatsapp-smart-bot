from pydantic import BaseSettings

class Settings(BaseSettings):
    TWILIO_SID: str
    TWILIO_AUTH: str
    TWILIO_WHATSAPP_NUMBER: str
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

    class Config:
        env_file = ".env"

settings = Settings()
