from contextlib import asynccontextmanager
from os import getenv
from redis.asyncio import Redis

TTL_SECONDS = 3600


class TokenStream:
    """Live copy of a reply's tokens, one Redis stream per message."""

    def __init__(self, redis: Redis, message_id: str):
        self.redis = redis
        self.key = message_id

    async def chunk(self, text: str):
        await self.redis.xadd(self.key, {"type": "chunk", "data": text})

    async def end(self):
        await self.redis.xadd(self.key, {"type": "end", "data": ""})
        await self.redis.expire(self.key, TTL_SECONDS)

    async def fail(self):
        await self.redis.xadd(self.key, {"type": "error", "data": ""})
        await self.redis.expire(self.key, TTL_SECONDS)


@asynccontextmanager
async def token_stream(message_id: str):
    async with Redis(
        host=getenv("REDIS_HOST", "localhost"),
        port=int(getenv("REDIS_PORT", "6379")),
        db=int(getenv("REDIS_DB", "0")),
        password=getenv("REDIS_PASSWORD"),
        decode_responses=True,
    ) as redis:
        yield TokenStream(redis, message_id)
