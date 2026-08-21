from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def tasks_list_keyboard(tasks):
    """Клавиатура списка заданий."""

    builder = InlineKeyboardBuilder()

    for task in tasks:

        builder.row(
            InlineKeyboardButton(
                text=(
                    f"📝 {task.title} — "
                    f"{task.reward} ₽Z"
                ),
                callback_data=(
                    f"task_assignment:{task.id}"
                ),
            )
        )

    # builder.row(
    #     InlineKeyboardButton(
    #         text="🏠 Главное меню",
    #         callback_data="main_menu",
    #     )
    # )

    return builder.as_markup()

def task_keyboard(task_id: int):
    """Клавиатура конкретного задания."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Взять задание",
            callback_data=f"take_task:{task_id}",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="tasks",
        ),
    )

    return builder.as_markup()


def taken_task_keyboard(task_id: int):
    """Клавиатура взятого задания."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🔗 Отправить результат",
            callback_data=f"submit_task:{task_id}",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Мои задания",
            callback_data="my_tasks",
        ),
    )

    return builder.as_markup()


def back_to_tasks_keyboard():
    """Кнопка возврата к заданиям."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="⬅️ К заданиям",
            callback_data="tasks",
        ),
    )

    return builder.as_markup()


def task_taken_keyboard(task_id: int):
    """Клавиатура взятого задания."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Мои задания",
            callback_data="my_tasks",
        )
    )

    # builder.row(
    #     InlineKeyboardButton(
    #         text="🏠 Главное меню",
    #         callback_data="main_menu",
    #     )
    # )

    return builder.as_markup()