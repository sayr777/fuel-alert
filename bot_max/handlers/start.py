from __future__ import annotations

from api_client import ApiClient
from client import MaxClient
from config import get_settings
from fsm import MaxFSM
from keyboards import main_menu

settings = get_settings()

WELCOME = (
    "Привет! Я **Топливный Дозор** — бот для сообщений о ситуации на АЗС.\n\n"
    "Здесь можно сообщить об отсутствии топлива, очереди, закрытой заправке и других "
    "проблемах. Обращение появится на общей карте, чтобы помочь другим водителям.\n\n"
    f"Карта: {settings.map_url}"
)

HELP_TEXT = (
    "**Как отправить обращение:**\n\n"
    "1. Нажмите «📢 Сообщить о ситуации»\n"
    "2. Выберите тип события\n"
    "3. Укажите марки топлива (если нужно)\n"
    "4. Отправьте геолокацию АЗС\n"
    "5. Прикрепите до 2 фото (необязательно)\n"
    "6. Добавьте комментарий (необязательно)\n"
    "7. Подтвердите отправку\n\n"
    f"Карта событий: {settings.map_url}"
)


async def handle_start(
    user_id: int,
    nickname: str | None,
    client: MaxClient,
    api: ApiClient,
    fsm: MaxFSM,
) -> None:
    await fsm.clear(user_id)
    try:
        await api.register_user(user_id, nickname)
    except Exception:
        pass
    await client.send_message(user_id, WELCOME, main_menu())
