from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить правило")],
            [KeyboardButton(text="📋 Просмотр конфига")],
            [KeyboardButton(text="🗑️ Удалить правило")],
            # [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
