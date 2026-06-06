# WhatsApp Smart Bot (MVP)

This repository contains a minimal WhatsApp bot scaffold that:

- Receives WhatsApp messages via Twilio webhooks
- Classifies messages by urgency (high / medium / low)
- Stores short-lived conversation context in Redis
- Generates contextual replies (template + LLM hook)

Quick start

1. Copy `.env.example` to `.env` and fill in the values (TWILIO keys, REDIS_URL, OPENAI_API_KEY, etc.).
2. Start Redis (or use a hosted Redis instance).
3. Install dependencies:

   pip install -r requirements.txt

4. Run the app locally:

   uvicorn app.main:app --reload --port 8000

5. Configure Twilio WhatsApp sandbox webhook (or your WhatsApp provider) to point to:

   https://<your-host>/webhook

Notes

- The urgency classifier is a simple rule-based implementation. Replace with an ML model (scikit-learn or transformer) when ready.
- The reply generator includes a placeholder for OpenAI. Set OPENAI_API_KEY to enable LLM-powered replies.
- Store credentials in environment variables or a secrets manager in production.
