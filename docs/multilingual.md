# Multilingual voice support notes

This doc explains how multilingual support is implemented and how it is used in the voice pipeline.

Key points

- Language detection: `app.lang_detect.detect_language()` (langdetect) is used to detect language codes (ISO 639-1) from transcripts or text messages.
- STT: OpenAI Whisper transcribes audio and we detect language from the transcript. The worker pipeline receives (transcript, lang).
- LLM: generate_reply(...) takes an optional `lang` parameter and instructs the LLM to reply in that language.
- TTS: synthesize_preferred(text, lang) tries ElevenLabs first and falls back to Google Cloud TTS (if enabled) for wider language coverage.
- Conversation store: language codes are persisted with messages so the system can reuse the user's last-known language when detection is unreliable.

Configuration

- Install langdetect: `pip install langdetect`
- Optional: enable Google TTS fallback by setting `GOOGLE_TTS_ENABLED=true` and providing Google credentials (google-cloud-texttospeech package and GOOGLE_APPLICATION_CREDENTIALS env var).

Best practices

- For short or single-word audio, language detection may be unreliable. The worker will fall back to the user's last detected language (if available) or 'en'.
- Monitor `stt_language_detected_total` metrics to see which languages are common and tune TTS voices accordingly.
