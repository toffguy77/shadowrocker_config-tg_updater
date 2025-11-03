from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить правило"), KeyboardButton(text="🗑️ Удалить правило")],
            [KeyboardButton(text="📋 Просмотр конфига")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
