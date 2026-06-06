from twilio.rest import Client
from app.config import settings

client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)

def send_whatsapp_message(to: str, body: str):
    # Twilio expects 'whatsapp:+12345' formatted numbers
    client.messages.create(
        body=body,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=to
    )
