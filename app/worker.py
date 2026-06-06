import asyncio
import logging
import tempfile
from typing import Any, Dict
from app.reply_generator import generate_reply
from app.messaging import client as messaging_client
from app.metrics_extra import set_worker_queue_depth, inc_message_retry, inc_llm_calls
from app.parse_message import normalize_message
from app.audio_stt import transcribe_audio_openai, convert_to_ogg_opus_async
from app.audio_tts import synthesize_eleven
from app.s3_utils import upload_bytes_to_s3
from app.config import settings
from app.convo_store import ConvoStore

logger = logging.getLogger(__name__)
store = ConvoStore(redis_url=settings.REDIS_URL)

class Worker:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Background worker started")

    async def stop(self):
        if not self._running:
            return
        self._running = False
        # push sentinel to wake the worker and let it exit
        await self.queue.put(None)
        if self._task:
            await self._task
        logger.info("Background worker stopped")

    async def _run(self):
        while True:
            # update queue depth metric
            try:
                set_worker_queue_depth(self.queue.qsize())
            except Exception:
                pass
            item = await self.queue.get()
            if item is None:
                # sentinel to stop
                break
            try:
                await self._process_item(item)
            except Exception:
                logger.exception("Worker failed to process item")
            finally:
                try:
                    self.queue.task_done()
                except Exception:
                    pass

    async def _process_item(self, item: Dict[str, Any]):
        """Process a queued message: detect audio, transcribe, generate reply and send audio/text."""
        from_number = item.get("from")
        body = item.get("body", "")
        history = item.get("history", [])
        provider = item.get("provider", getattr(settings, "WHATSAPP_PROVIDER", "twilio"))
        media = item.get("media") or []

        # If there's audio media, handle STT -> LLM -> TTS flow
        audio_media = None
        for m in media:
            mtype = (m.get("type") or "").lower()
            if mtype.startswith("audio") or mtype in ("voice", "voice_note", "ogg", "opus"):
                audio_media = m
                break

        transcript = None
        if audio_media:
            try:
                # Determine how to obtain bytes: normalized 'raw' media may include url or id
                # Prefer raw.url or raw['url'] or media.get('url') else media.get('id') for Meta
                media_url = audio_media.get('url') or audio_media.get('media_url')
                media_id = audio_media.get('id')
                media_bytes = None

                # If provider is meta and we have id, fetch via Meta media endpoint
                if provider == 'meta' and media_id:
                    # Use Meta client to fetch media URL
                    import requests
                    meta_token = settings.META_TOKEN
                    # GET /{media_id}?access_token={token}
                    meta_media_url = f"https://graph.facebook.com/v15.0/{media_id}?access_token={meta_token}"
                    r = requests.get(meta_media_url, timeout=10)
                    r.raise_for_status()
                    data = r.json()
                    fetch_url = data.get('url')
                    r2 = requests.get(fetch_url, timeout=20)
                    r2.raise_for_status()
                    media_bytes = r2.content
                elif media_url:
                    import requests
                    # Twilio media URLs may require basic auth
                    try:
                        auth = None
                        if settings.TWILIO_SID and settings.TWILIO_AUTH:
                            auth = (settings.TWILIO_SID, settings.TWILIO_AUTH)
                        r = requests.get(media_url, timeout=20, auth=auth)
                        r.raise_for_status()
                        media_bytes = r.content
                    except Exception:
                        logger.exception("Failed to fetch media url %s", media_url)
                else:
                    logger.warning("No media URL or id found for audio media")

                if not media_bytes:
                    raise RuntimeError("Could not fetch audio bytes")

                # Convert to opus-in-ogg for better compatibility
                converted = await convert_to_ogg_opus_async(media_bytes)

                # Transcribe
                transcript = await transcribe_audio_openai(converted, mime_type='audio/ogg')
                # append transcript to convo store
                await store.append_message(from_number, {"text": transcript, "type": "voice"})
            except Exception:
                logger.exception("Audio STT failed")
                transcript = None

        # Build prompt text: use transcript if present else body
        prompt_text = (transcript or body or "").strip()
        # include recent history
        if history:
            # history is an array of dicts; include last N texts
            recent = [h.get('text') for h in history if h.get('text')]
            # include as context
            context = "\n".join(recent[-settings.LLM_MAX_HISTORY_MESSAGES:])
        else:
            context = ""

        combined = (context + "\n" + prompt_text).strip() if context else prompt_text

        # Generate reply text (LLM)
        try:
            reply_text = await generate_reply(combined, history)
            inc_llm_calls(True)
        except Exception:
            logger.exception("LLM reply generation failed")
            inc_llm_calls(False)
            reply_text = "Thanks — I received your message. Can you tell me more?"

        # If we have TTS configured and we received audio, synthesize audio reply and send audio
        if audio_media:
            try:
                # Synthesize using ElevenLabs (blocking) in thread
                loop = asyncio.get_event_loop()
                tts_bytes, mime = await loop.run_in_executor(None, synthesize_eleven, reply_text)
                # Convert to opus if needed
                converted_tts = await convert_to_ogg_opus_async(tts_bytes)

                if provider == 'meta':
                    # Upload to Meta and send audio message
                    from app.meta_client import MetaProvider
                    meta = MetaProvider()
                    media_id = meta.upload_media(converted_tts, mime_type='audio/ogg')
                    # send audio message
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": from_number.replace('whatsapp:', ''),
                        "type": "audio",
                        "audio": {"id": media_id}
                    }
                    # POST to messages endpoint
                    import requests
                    headers = {"Authorization": f"Bearer {settings.META_TOKEN}", "Content-Type": "application/json"}
                    r = requests.post(f"https://graph.facebook.com/v15.0/{settings.META_PHONE_NUMBER_ID}/messages", headers=headers, json=payload, timeout=10)
                    r.raise_for_status()
                else:
                    # Upload to S3 and send via Twilio with media_url
                    url = upload_bytes_to_s3(converted_tts, 'audio/ogg')
                    await asyncio.to_thread(messaging_client.send, to=from_number, body=reply_text)  # send text + media
                    # Twilio's send wrapper may not accept media url; use underlying client if available
                    try:
                        # prefer low-level twilio client
                        tw = messaging_client._client
                        tw.send(to=from_number, body=reply_text)
                    except Exception:
                        # fallback to TwilioProvider via messaging_client
                        try:
                            await asyncio.to_thread(messaging_client.send, to=from_number, body=reply_text)
                        except Exception:
                            logger.exception("Failed to send text via messaging client")
                    # If provider supports media_url param, attempt to call Twilio directly
                    try:
                        from app.twilio_client import TwilioProvider
                        tprov = TwilioProvider()
                        # Twilio SDK: messages.create(body=..., from_=..., to=..., media_url=[url])
                        await asyncio.to_thread(tprov.client.messages.create, body=reply_text, from_=settings.TWILIO_WHATSAPP_NUMBER, to=from_number, media_url=[url])
                    except Exception:
                        logger.exception("Failed to send Twilio media message")

                # Persist reply to convo store
                await store.append_message(from_number, {"text": reply_text, "type": "voice_reply"})
            except Exception:
                logger.exception("Failed to synthesize/send audio reply; falling back to text")
                try:
                    await asyncio.to_thread(messaging_client.send, to=from_number, body=reply_text)
                except Exception:
                    logger.exception("Failed to send fallback text reply")
        else:
            # No audio: send text reply as before
            try:
                await asyncio.to_thread(messaging_client.send, to=from_number, body=reply_text)
                # persist
                await store.append_message(from_number, {"text": reply_text, "type": "bot_reply"})
            except Exception:
                logger.exception("Failed to send message to %s", from_number)
                try:
                    inc_message_retry(getattr(messaging_client, "_client", type(messaging_client)).__class__.__name__)
                except Exception:
                    inc_message_retry("unknown")

    async def enqueue(self, item: Dict[str, Any]):
        await self.queue.put(item)


# singleton worker instance to be used by the app
worker = Worker()
