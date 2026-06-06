import asyncio
import logging
from typing import Any, Dict
from app.reply_generator import generate_reply
from app.messaging import client as messaging_client

logger = logging.getLogger(__name__)

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
        """Process a queued message: generate reply and send it."""
        from_number = item.get("from")
        body = item.get("body", "")
        history = item.get("history", [])

        # Generate reply (may internally call blocking code via run_in_executor)
        try:
            reply = await generate_reply(body, history)
        except Exception:
            logger.exception("Failed to generate reply; using fallback")
            reply = "Thanks — I received your message. Can you tell me more?"

        # Send message (messaging_client.send may be blocking -> run in thread)
        try:
            await asyncio.to_thread(messaging_client.send, to=from_number, body=reply)
        except Exception:
            logger.exception("Failed to send message to %s", from_number)

    async def enqueue(self, item: Dict[str, Any]):
        await self.queue.put(item)


# singleton worker instance to be used by the app
worker = Worker()
