# bot/handlers/tasks.py

from io import BytesIO

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

@router.callback_query(F.data == "tasks") # Это надо для возврата в меню
async def back_to_tasks(callback: CallbackQuery):
    tasks = await get_available_tasks(callback.from_user.id)

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

    tasks = await get_available_tasks(message.from_user.id)
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
    text = (
        f"Вы выбрали задание {task.platform} \n\n"
        f"Город: {task.city} \n\n"
        f"Сфера: {task.sphera} \n\n"
        f"Цена: {task.reward} ₽ \n\n"
        "Выполнение задания занимает около 5-10 минут!\n\n"
    )

    builder.row(
            InlineKeyboardButton(
                text='Взять задание',
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
            text,
            reply_markup=builder.as_markup(),
        )


@router.callback_query(F.data.startswith("show_task:"))
async def show_task(callback: CallbackQuery):
    """Показывает выбранное задание."""

    task_id = int(callback.data.split(":")[1])
    
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
            text="✅ Далее",
            callback_data=f"show_task2:{task.id}",
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


@router.callback_query(F.data.startswith("show_task2:"))
async def show_task2(callback: CallbackQuery):
    """Показывает выбранное задание."""

    task_id = int(callback.data.split(":")[1])
    
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


    text = (
        f"{task.description2}\n\n"
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
    await state.set_state(TaskStates.waiting_review_screenshot)
    await update_task_completions(task_id)

    await callback.message.answer(
        "🔗 Отправьте скриншот:"
    )

    await callback.answer()
    # await callback.answer("✅ Задание выполнено!")

from pathlib import Path

from django.conf import settings


@router.message(
    TaskStates.waiting_review_screenshot,
    F.photo,
)
async def process_review_screenshot(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    task_id = data["task_id"]

    photo = message.photo[-1]

    # Получаем информацию о файле в Telegram
    file = await message.bot.get_file(photo.file_id)

    # Куда сохраняем локально
    reviews_dir = Path(settings.MEDIA_ROOT) / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    file_path = reviews_dir / f"{photo.file_id}.jpg"

    print("Сохраняем в:", file_path)
    print("Telegram file:", file.file_path)

    # ВАЖНО: скачиваем из Telegram
    await message.bot.download_file(
        file.file_path,
        destination=file_path,
    )

    # Проверяем, действительно ли файл появился
    print("Существует:", file_path.exists())
    print("Размер:", file_path.stat().st_size if file_path.exists() else 0)

    screenshot_path = f"reviews/{file_path.name}"

    success, text = await complete_task(
        telegram_id=message.from_user.id,
        task_id=task_id,
        review_url="",
        screenshot=screenshot_path,
    )

    if success:
        await state.clear()

    await message.answer(text)

@router.message(TaskStates.waiting_review_screenshot)
async def invalid_screenshot(message: Message):
    await message.answer(
        "❌ Нужно отправить именно изображение."
    )


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


#########

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