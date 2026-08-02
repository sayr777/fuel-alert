import logging
from typing import Any

import aiohttp

MAX_API = "https://platform-api2.max.ru"

logger = logging.getLogger(__name__)


class MaxClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._session: aiohttp.ClientSession | None = None

    async def _sess(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            # platform-api2.max.ru uses a Russian government CA not in standard bundles
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(
                base_url=MAX_API,
                headers={"Authorization": self._token},
                connector=connector,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_updates(self, marker: int | None = None, timeout: int = 30) -> dict:
        sess = await self._sess()
        params: dict[str, Any] = {"timeout": timeout, "limit": 100}
        if marker is not None:
            params["marker"] = marker
        async with sess.get("/updates", params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def send_message(
        self,
        user_id: int,
        text: str,
        keyboard: list[list[dict]] | None = None,
    ) -> dict:
        sess = await self._sess()
        body: dict[str, Any] = {"text": text, "format": "markdown"}
        if keyboard:
            body["attachments"] = [
                {"type": "inline_keyboard", "payload": {"buttons": keyboard}}
            ]
        async with sess.post("/messages", params={"user_id": user_id}, json=body) as resp:
            if not resp.ok:
                logger.warning("send_message error %s: %s", resp.status, await resp.text())
            return await resp.json() if resp.ok else {}

    async def answer_callback(
        self,
        callback_id: str,
        text: str | None = None,
        keyboard: list[list[dict]] | None = None,
    ) -> None:
        """Answer a callback and optionally update the original message."""
        sess = await self._sess()
        body: dict[str, Any] = {}
        if text is not None or keyboard is not None:
            msg: dict[str, Any] = {}
            if text is not None:
                msg["text"] = text
                msg["format"] = "markdown"
            if keyboard:
                msg["attachments"] = [
                    {"type": "inline_keyboard", "payload": {"buttons": keyboard}}
                ]
            body["message"] = msg
        async with sess.post("/answers", params={"callback_id": callback_id}, json=body) as resp:
            if not resp.ok:
                logger.debug("answer_callback %s: %s", resp.status, await resp.text())

    async def set_commands(self, commands: list[dict]) -> None:
        sess = await self._sess()
        async with sess.patch("/me/commands", json={"commands": commands}) as resp:
            if not resp.ok:
                logger.warning("set_commands error %s: %s", resp.status, await resp.text())

    async def download_bytes(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()
