import json

import redis.asyncio as aioredis

_PREFIX = "max_fsm"
_TTL = 3600


class MaxFSM:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._r = redis

    def _sk(self, user_id: int) -> str:
        return f"{_PREFIX}:{user_id}:state"

    def _dk(self, user_id: int) -> str:
        return f"{_PREFIX}:{user_id}:data"

    async def get_state(self, user_id: int) -> str | None:
        val = await self._r.get(self._sk(user_id))
        return val.decode() if val else None

    async def set_state(self, user_id: int, state: str) -> None:
        await self._r.set(self._sk(user_id), state, ex=_TTL)

    async def get_data(self, user_id: int) -> dict:
        val = await self._r.get(self._dk(user_id))
        return json.loads(val) if val else {}

    async def update_data(self, user_id: int, **kwargs) -> None:
        data = await self.get_data(user_id)
        data.update(kwargs)
        await self._r.set(self._dk(user_id), json.dumps(data, ensure_ascii=False), ex=_TTL)

    async def clear(self, user_id: int) -> None:
        await self._r.delete(self._sk(user_id), self._dk(user_id))
