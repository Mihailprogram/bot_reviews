from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from asgiref.sync import sync_to_async

from bot.models import TelegramUser

from bot.services.tasks import get_user_tasks, complete_task
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton



router = Router()


@sync_to_async
def get_balance(telegram_id: int):

    try:
        user = TelegramUser.objects.get(
            telegram_id=telegram_id,
        )
    except TelegramUser.DoesNotExist:
        return None

    return user.balance


# @router.callback_query(F.data == "balance")
@router.message(F.text == "💰 Баланс")
async def balance_handler(
    # callback: CallbackQuery,
    message: Message
):
    """Показывает баланс."""
    builder = InlineKeyboardBuilder()

    balance = await get_balance(
        message.from_user.id
    )

    if balance is None:
        await message.answer(
            "Пользователь не найден.",
            show_alert=True,
        )
        return

    # builder.row(
    #         InlineKeyboardButton(
    #             text="🏠 Главное меню",
    #             callback_data="main_menu",
    #         )
    #     )
    await message.answer(
        (
            "💰Ваш баланс\n\n"
            f"Доступно: {balance} ₽"
        ),

        reply_markup=builder.as_markup(),
    )
    await message.answer()


# @router.callback_query(F.data == "my_tasks")
@router.message(F.text == "📌 Мои задания")
async def my_tasks_handler(
    # callback: CallbackQuery,
    message: Message
):
    """Показывает задания пользователя."""

    user_tasks = await get_user_tasks(
        message.from_user.id
    )
    builder = InlineKeyboardBuilder()
    # builder.row(
    #             InlineKeyboardButton(
    #                 text="🏠 Главное меню",
    #                 callback_data="main_menu",
    #             )
    #         )

    if not user_tasks:
        await message.answer(
            "📭 Вы пока не брали заданий.",
            reply_markup=builder.as_markup(),
        )

        await message.answer()
        return

    status_names = {
        "taken": "🟡 Выполняется",
        "submitted": "🔵 На проверке",
        "approved": "🟢 Выполнено",
        "rejected": "🔴 Отклонено",
    }

    text = "📌 Мои задания\n\n"

    for user_task in user_tasks:

        status = status_names.get(
            user_task.status,
            user_task.status,
        )

        text += (
            f"📝{user_task.task.title}\n"
            f"Статус: {status}\n"
            f"💰 {user_task.task.reward} ₽\n\n"
        )

    await message.answer(
        text, 
        reply_markup=builder.as_markup(),
    )

    await message.answer()

    