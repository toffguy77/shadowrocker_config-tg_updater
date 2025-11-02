from aiogram.utils.keyboard import InlineKeyboardBuilder


def pager(prefix: str, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if has_prev:
        kb.button(text="⬅️", callback_data=f"{prefix}:page:{page-1}")
    if has_next:
        kb.button(text="➡️", callback_data=f"{prefix}:page:{page+1}")
    return kb
