from pydantic import BaseSettings

class Settings(BaseSettings):
    TWILIO_SID: str
    TWILIO_AUTH: str
    TWILIO_WHATSAPP_NUMBER: str
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    PORT: int = 8000
    WEBHOOK_SECRET_TOKEN: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
