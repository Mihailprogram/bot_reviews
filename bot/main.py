import asyncio
import os

import django
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from aiogram.client.session.aiohttp import AiohttpSession

# Загружаем настройки Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "base.settings",
)

# Инициализируем Django
django.setup()

load_dotenv()

from bot.handlers import profile, start, tasks  # noqa: E402

from aiogram.types import BotCommand


async def set_commands(bot: Bot) -> None:
    """Устанавливает команды бота в меню Telegram."""

    commands = [
        BotCommand(
            command="start",
            description="Запустить бота",
        ),
        BotCommand(
            command="tasks",
            description="Доступные задания",
        ),
        BotCommand(
            command="my_tasks",
            description="Мои задания",
        ),
        BotCommand(
            command="profile",
            description="Мой профиль",
        ),
        BotCommand(
            command="balance",
            description="Мой баланс",
        ),
        BotCommand(
            command="help",
            description="Помощь",
        ),
    ]

    await bot.set_my_commands(commands)

async def main() -> None:
    """Запускает Telegram-бота."""
    
    session = AiohttpSession(proxy="http://202.28.194.139:31280")

    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError(
            "BOT_TOKEN не найден в переменных окружения"
        )

    bot = Bot(token=token, session=session)

    await set_commands(bot)

    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(profile.router)

    print("🤖 Bot started")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())