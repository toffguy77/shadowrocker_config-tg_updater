from aiogram.utils.keyboard import InlineKeyboardBuilder


def confirm_add_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Добавить", callback_data="add:confirm:add")
    kb.button(text="❌ Отменить", callback_data="add:confirm:cancel")
    kb.adjust(2)
    return kb


def confirm_replace_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Заменить", callback_data="add:confirm:replace")
    kb.button(text="⬅️ Оставить", callback_data="add:confirm:keep")
    kb.button(text="❌ Отменить", callback_data="add:confirm:cancel")
    kb.adjust(2)
    return kb
