# Voice support documentation

This document describes how voice (voice notes / audio messages) are handled by the bot.

Overview

- Incoming voice notes are detected by `app.parse_message.normalize_message()` and included as `media` entries in the normalized message.
- The background worker downloads the audio, converts it to opus/ogg using `ffmpeg` (if available), transcribes it via OpenAI Whisper (`app.audio_stt`), appends the transcript to the conversation store, runs the LLM reply generator (with conversation context), synthesizes the reply using ElevenLabs (`app.audio_tts`), and sends the audio reply back to the sender (Meta via media upload, Twilio via S3-hosted media URL).

Environment variables (add to `.env`)

- OPENAI_API_KEY - required for STT (Whisper) and LLM replies
- ELEVENLABS_API_KEY - required for ElevenLabs TTS
- S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY - required for hosting media for Twilio
- META_TOKEN, META_PHONE_NUMBER_ID - required for Meta uploads & sends

Requirements

- ffmpeg must be installed on the worker host for reliable audio format conversion. If ffmpeg is not present, the worker will attempt to use the original audio bytes.
- boto3 (for S3 uploads)
- requests and openai python SDK

Notes & privacy

- Ensure you have consent to transcribe and synthesize users' voice messages.
- Transcripts and audio replies are stored in the conversation store (Redis) by default; configure retention and access controls as needed.

Testing

- You can test by sending a voice note to the WhatsApp sandbox (Twilio) or via Meta; the webhook will put a job on the queue and the worker will process it. Monitor logs for STT/TTS steps.
