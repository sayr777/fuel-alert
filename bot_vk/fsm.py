import json
from redis.asyncio import Redis


class VkFSM:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "vk_fsm"
        self.ttl = 3600

    def _key(self, user_id: int, suffix: str) -> str:
        return f"{self.prefix}:{user_id}:{suffix}"

    async def get_state(self, user_id: int) -> str | None:
        val = await self.redis.get(self._key(user_id, "state"))
        return val.decode() if val else None

    async def set_state(self, user_id: int, state: str) -> None:
        await self.redis.setex(self._key(user_id, "state"), self.ttl, state)

    async def clear(self, user_id: int) -> None:
        await self.redis.delete(self._key(user_id, "state"), self._key(user_id, "data"))

    async def get_data(self, user_id: int) -> dict:
        val = await self.redis.get(self._key(user_id, "data"))
        return json.loads(val) if val else {}

    async def update_data(self, user_id: int, **kwargs) -> None:
        data = await self.get_data(user_id)
        data.update(kwargs)
        await self.redis.setex(self._key(user_id, "data"), self.ttl, json.dumps(data))
