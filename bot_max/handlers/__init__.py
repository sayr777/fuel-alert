from __future__ import annotations

import logging

from api_client import ApiClient
from client import MaxClient
from fsm import MaxFSM
from handlers.report import handle_callback, handle_message
from handlers.start import handle_start

logger = logging.getLogger(__name__)


async def dispatch_update(
    update: dict,
    client: MaxClient,
    api: ApiClient,
    fsm: MaxFSM,
) -> None:
    update_type = update.get("update_type")

    if update_type == "bot_started":
        user = update.get("user", {})
        user_id: int = user.get("user_id", 0)
        nickname = user.get("username") or user.get("first_name")
        await handle_start(user_id, nickname, client, api, fsm)

    elif update_type == "message_callback":
        cb = update.get("callback", {})
        user_id = cb.get("user", {}).get("user_id", 0)
        callback_id: str = cb.get("callback_id", "")
        payload: str = cb.get("payload", "")
        await handle_callback(user_id, callback_id, payload, client, api, fsm)

    elif update_type == "message_created":
        user = update.get("user", {})
        user_id = user.get("user_id", 0)
        nickname = user.get("username") or user.get("first_name")
        body = update.get("message", {}).get("body", {})
        text: str = body.get("text") or ""
        attachments: list[dict] = body.get("attachments") or []

        if _is_command(text, "start") or _is_command(text, "help"):
            await handle_start(user_id, nickname, client, api, fsm)
        else:
            await handle_message(user_id, text, attachments, client, api, fsm)

    # Ignore: bot_stopped, bot_added, bot_removed, message_edited, etc.


def _is_command(text: str, cmd: str) -> bool:
    t = text.strip()
    return t == f"/{cmd}" or t.startswith(f"/{cmd} ") or t.startswith(f"/{cmd}@")
