from aiogram.utils.keyboard import InlineKeyboardBuilder


def policy_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Через прокси", callback_data="add:policy:PROXY")
    kb.button(text="⚡ Напрямую", callback_data="add:policy:DIRECT")
    kb.button(text="🚫 Блокировать", callback_data="add:policy:REJECT")
    kb.adjust(1)
    kb.button(text="⬅️ Назад", callback_data="add:back:type")
    return kb
