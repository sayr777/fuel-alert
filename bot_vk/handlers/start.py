from vkbottle.bot import Message


async def handle_start(message: Message, api_client, fsm, keyboard_fn) -> None:
    user_id = message.from_id
    await api_client.register_user(user_id, f"vk_{user_id}")
    await fsm.clear(user_id)
    await message.answer(
        "👋 Добро пожаловать в Топливный Дозор!\n\n"
        "Помогите другим водителям — сообщите о проблемах с топливом на АЗС.\n"
        "Нажмите «📢 Сообщить о ситуации» чтобы начать.",
        keyboard=keyboard_fn(),
    )
