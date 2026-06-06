import aioredis
import json
from typing import List

class ConvoStore:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def append_message(self, user_id: str, message: dict):
        key = f"convo:{user_id}"
        await self.redis.rpush(key, json.dumps(message))
        await self.redis.expire(key, 60 * 60 * 24)  # keep 24h by default

    async def get_history(self, user_id: str, limit: int = 20) -> List[dict]:
        key = f"convo:{user_id}"
        items = await self.redis.lrange(key, -limit, -1)
        return [json.loads(i) for i in items]
