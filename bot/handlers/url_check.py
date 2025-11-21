from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.github_store import GitHubFileStore

router = Router()


@router.message(Command("urlcheck"))
@router.message(F.text == "🔍 Проверка URL")
async def url_check_command(m: Message, store: GitHubFileStore) -> None:
    try:
        fetched = await store.fetch(file_path="url_check.log")
        log_content = fetched["text"]
        
        if not log_content or log_content.strip() == "":
            await m.answer("📋 Лог проверки URL пуст")
            return
        
        lines = log_content.strip().split("\n")
        
        # Parse log for errors
        errors = []
        for line in lines:
            if "ERROR" in line or "unreachable" in line or "HTTP" in line and ("404" in line or "500" in line):
                errors.append(line)
        
        if not errors:
            await m.answer("✅ <b>Все URL доступны</b>\n\nПоследняя проверка прошла успешно")
            return
        
        # Format errors
        msg_lines = ["⚠️ <b>Недоступные URL</b>\n"]
        for err in errors[:20]:  # Limit to 20
            msg_lines.append(f"<code>{err[:100]}</code>")
        
        if len(errors) > 20:
            msg_lines.append(f"\n... и ещё {len(errors) - 20} ошибок")
        
        await m.answer("\n".join(msg_lines))
    except Exception:
        await m.answer("❌ Лог проверки URL не найден или недоступен")
