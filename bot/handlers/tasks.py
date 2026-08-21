# bot/handlers/tasks.py

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from asgiref.sync import sync_to_async
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from bot.models import Task
from bot.keyboards.tasks import tasks_list_keyboard, task_taken_keyboard
from bot.services.tasks import get_available_tasks, update_task_completions
from bot.keyboards.main import main_keyboard
from bot.services.tasks import take_task, get_task, complete_task
from bot.states import TaskStates


router = Router()


@sync_to_async
def get_tasks():

    return list(
        Task.objects.filter(
            is_active=True,
        )
        .order_by("-created_at")[:10]
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery) -> None:
    """Возвращает пользователя в главное меню."""

    await callback.answer()

@router.callback_query(F.data == "tasks")
async def back_to_tasks(callback: CallbackQuery):
    tasks = await get_available_tasks()

    if not tasks:
        await callback.message.edit_text(
            "😔 Сейчас доступных заданий нет."
        )
        await callback.answer()
        return

    text = (
        "📋 Доступные задания\n\n"
        "Выберите задание:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=tasks_list_keyboard(tasks),
    )

    await callback.answer()

@router.message(F.text == "📋 Задания")
async def show_tasks(
    # callback: CallbackQuery
    message: Message
    ):
    """Показывает список заданий."""

    tasks = await get_available_tasks()
    builder = InlineKeyboardBuilder()

    if not tasks:
        await message.answer(
            "😔 Сейчас доступных заданий нет.",
            reply_markup=builder.as_markup()
        )

        # await message.answer()
        return

    text = (
        "📋Доступные задания\n\n"
        "Выберите задание:"
    )

    await message.answer(
        text,
        reply_markup=tasks_list_keyboard(tasks),
    )



# Инлайн Кнопки заданий 
@router.callback_query(F.data.startswith("task_assignment:"))
async def task_assignment(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    builder = InlineKeyboardBuilder()

    task = await get_task(task_id)
    builder.row(
            InlineKeyboardButton(
                text="Взять задание",
                callback_data=f"show_task:{task.id}",
            )
        )
    builder.row(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="tasks",
            )
        )
    await callback.message.edit_text(
            "Подтвердите выбор",
            reply_markup=builder.as_markup(),
        )


@router.callback_query(F.data.startswith("show_task:"))
async def show_task(callback: CallbackQuery):
    """Показывает выбранное задание."""

    task_id = int(callback.data.split(":")[1])
    print("task_id---",task_id)
    await take_task(telegram_id=callback.from_user.id,
            task_id=task_id,)

    task = await get_task(task_id)

    if task is None:
        await callback.answer(
            "Задание больше недоступно.",
            show_alert=True,
        )
        return

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Готово",
            callback_data=f"complete_task:{task.id}",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="tasks",
        )
    )


    text = (
        f"📝 {task.title}\n\n"
        f"{task.description}\n\n"
        f"💰 Вознаграждение: {task.reward} ₽"
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("complete_task:"))
async def complete_task_start(callback: CallbackQuery, state: FSMContext):
    """Отмечает задание выполненным."""

    task_id = int(callback.data.split(":")[1])

    await state.update_data(task_id=task_id)
    await state.set_state(TaskStates.waiting_review_url)
    await update_task_completions(task_id)

    await callback.message.answer(
        "🔗 Отправьте ссылку на ваш отзыв:"
    )

    await callback.answer()
    print("ИИИ")
    # await callback.answer("✅ Задание выполнено!")


@router.message(TaskStates.waiting_review_url)
async def process_review_url(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    task_id = data["task_id"]

    review_url = message.text.strip()


    success, text = await complete_task(
        telegram_id=message.from_user.id,
        task_id=task_id,
        review_url=review_url,
    )

    
    builder = InlineKeyboardBuilder()

    # builder.row(
    #     InlineKeyboardButton(
    #         text="🏠 Главное меню",
    #         callback_data="main_menu",
    #     )
    # )

    await state.clear()
    await message.answer(
        text,
        reply_markup=builder.as_markup(),
    )



@router.callback_query(F.data.startswith("take_task:"))
async def take_task_handler(callback: CallbackQuery):
    """Берёт задание пользователем."""

    task_id = int(callback.data.split(":")[1])

    success, message, task = await take_task(
        telegram_id=callback.from_user.id,
        task_id=task_id,
    )

    if not success:
        await callback.answer(
            message,
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        (
            "✅ Задание взято!\n\n"
            f"📝 {task.title}\n\n"
            f"{task.description}\n\n"
            f"💰 Вознаграждение: {task.reward} ₽"
        ),
        reply_markup=task_taken_keyboard(task.id),
    )

    await callback.answer()