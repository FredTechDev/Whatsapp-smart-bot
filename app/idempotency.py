import aioredis
from app.config import settings

class IdempotencyStore:
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            # using redis-py's asyncio client (aioredis compatibility)
            self._redis = await aioredis.from_url(self.redis_url)
        return self._redis

    async def seen_or_set(self, key: str, ttl: int = 24 * 60 * 60) -> bool:
        """
        Atomically set key with NX and expiry. Return True if the key was already present (i.e., duplicate),
        False if we successfully set it (i.e., not duplicate).
        """
        redis = await self._get_redis()
        # redis.set returns True if set, None if key exists
        res = await redis.set(key, "1", ex=ttl, nx=True)
        if res:
            return False
        return True

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


# singleton
idempotency = IdempotencyStore()
