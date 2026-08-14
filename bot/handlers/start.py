# bot/handlers/start.py

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from asgiref.sync import sync_to_async

from bot.models import TelegramUser
from bot.keyboards.main import main_keyboard


router = Router()


@sync_to_async
def get_or_create_user(message: Message):

    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=message.from_user.id,
        defaults={
            "username": message.from_user.username or "",
            "first_name": message.from_user.first_name or "",
        },
    )

    return user


@router.message(CommandStart())
async def start(message: Message):

    await get_or_create_user(message)

    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Здесь вы можете получать задания "
        "и выполнять их за вознаграждение.",
        reply_markup=main_keyboard(),
    )


