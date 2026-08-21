# bot/keyboards/main.py

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# def main_keyboard():

#     builder = InlineKeyboardBuilder()

#     builder.row(
#         InlineKeyboardButton(
#             text="📋 Задания",
#             callback_data="tasks",
#         ),
#     )

#     builder.row(
#         InlineKeyboardButton(
#             text="📌 Мои задания",
#             callback_data="my_tasks",
#         ),
#     )

#     builder.row(
#         InlineKeyboardButton(
#             text="💰 Баланс",
#             callback_data="balance",
#         ),
#     )

#     return builder.as_markup()



def main_keyboard():
    keyboard = [
        [
            KeyboardButton(text="📋 Задания"),
        ],
        # [
        #     KeyboardButton(text="📌 Мои задания"),
        # ],
        [
            KeyboardButton(text="💰 Баланс"),
        ],
        [
            KeyboardButton(text="👤 Личный кабинет"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )