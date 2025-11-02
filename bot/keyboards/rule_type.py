from aiogram.utils.keyboard import InlineKeyboardBuilder


def rule_type_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Домен и поддомены", callback_data="add:type:DOMAIN-SUFFIX")
    kb.button(text="🎯 Точный домен", callback_data="add:type:DOMAIN")
    kb.button(text="🔍 Ключевое слово", callback_data="add:type:DOMAIN-KEYWORD")
    kb.button(text="🔢 IP-адрес/диапазон", callback_data="add:type:IP-CIDR")
    kb.adjust(1)
    kb.button(text="⬅️ Назад", callback_data="add:back:menu")
    return kb
