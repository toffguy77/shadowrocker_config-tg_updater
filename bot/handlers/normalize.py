from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.github_store import GitHubFileStore
from bot.services.rules_file import parse_text, render_lines

router = Router()


@router.message(Command("normalize"))
async def normalize_config(m: Message, store: GitHubFileStore) -> None:
    try:
        fetched = await store.fetch()
        lines = parse_text(fetched["text"])
        new_text = render_lines(lines)
        if new_text == fetched["text"]:
            await m.answer("✅ Конфиг уже нормализован (две колонки)")
            return
        resp = await store.commit(new_text, "Normalize: drop policy column", m.from_user.username if m.from_user else None, None, fetched["sha"])  
        url = resp.get("commit", {}).get("html_url")
        await m.answer(f"✅ Нормализовано. {('Коммит: ' + url) if url else ''}")
    except Exception as e:
        await m.answer(f"❌ Ошибка нормализации: {e}")
