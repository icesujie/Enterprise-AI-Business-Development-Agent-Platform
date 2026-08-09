from __future__ import annotations

from redis.asyncio import Redis


async def consume_fixed_window(
    *,
    redis_url: str,
    key: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int]:
    client = Redis.from_url(redis_url, decode_responses=True)
    try:
        async with client.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.ttl(key)
            count_value, ttl_value = await pipeline.execute()
        count = int(count_value)
        ttl = int(ttl_value)
        if ttl < 0:
            await client.expire(key, window_seconds)
            ttl = window_seconds
        return count <= limit, ttl
    finally:
        await client.aclose()
