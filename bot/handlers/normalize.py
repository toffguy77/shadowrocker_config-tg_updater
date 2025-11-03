from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.github_store import GitHubFileStore
from bot.services.rules_file import parse_text, render_lines

router = Router()


@router.message(Command("normalize"))
async def normalize_config(m: Message, store: GitHubFileStore) -> None:
    loading_msg = await m.answer("⌛ Нормализую...")
    try:
        fetched = await store.fetch()
        lines = parse_text(fetched["text"])
        new_text = render_lines(lines)
        if new_text == fetched["text"]:
            if loading_msg:
                await loading_msg.edit_text("✅ Конфиг уже нормализован")
            return
        resp = await store.commit(new_text, "Normalize: drop policy column", m.from_user.username if m.from_user else None, None, fetched["sha"])
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        url = resp.get("commit", {}).get("html_url")
        kb = InlineKeyboardBuilder()
        if url:
            kb.button(text="🔗 Посмотреть коммит", url=url)
        if loading_msg:
            await loading_msg.edit_text("✅ <b>Нормализовано</b>", reply_markup=kb.as_markup() if kb.buttons else None)
    except Exception:
        if loading_msg:
            await loading_msg.edit_text("❌ Ошибка нормализации")
