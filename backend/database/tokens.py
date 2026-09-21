from asyncio import get_running_loop
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import getenv
from redis.asyncio import Redis

OPEN_TTL_SECONDS = 600
BLOCK_MS = 5000
IDLE_TIMEOUT_SECONDS = 120


class TokenStreamError(Exception):
    """The worker reported that it could not finish the reply."""


class TokenStream:
    """Reader side of a reply's tokens, one Redis stream per message.

    The worker appends `chunk` entries and closes with `end` or `error`; see
    database.tokens in the worker codebase.
    """

    def __init__(self, redis: Redis, message_id: str):
        self.redis = redis
        self.key = message_id

    async def open(self):
        """Create the stream so readers can attach before the worker's first token.

        The expiry stops streams of messages that are never picked up from
        living forever; the worker extends it once the reply is finished.
        """
        await self.redis.xadd(self.key, {"type": "start", "data": ""})
        await self.redis.expire(self.key, OPEN_TTL_SECONDS)

    async def read(self) -> AsyncIterator[str]:
        """Yield the reply's chunks from the beginning until it ends.

        Reads without consumer groups, so any number of readers can follow the
        same message and none leaves state behind in Redis. Raises
        TokenStreamError if the worker failed, TimeoutError if nothing arrives
        for IDLE_TIMEOUT_SECONDS (worker gone, or the stream expired).
        """
        loop = get_running_loop()
        last_id = "0"
        deadline = loop.time() + IDLE_TIMEOUT_SECONDS
        while loop.time() < deadline:
            streams = await self.redis.xread({self.key: last_id}, count=100, block=BLOCK_MS)
            for _, entries in streams:
                for last_id, fields in entries:
                    deadline = loop.time() + IDLE_TIMEOUT_SECONDS
                    match fields.get("type"):
                        case "chunk":
                            yield fields["data"]
                        case "end":
                            return
                        case "error":
                            raise TokenStreamError(f"Reply {self.key} failed")
        raise TimeoutError(f"No tokens for {self.key} in {IDLE_TIMEOUT_SECONDS}s")


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
