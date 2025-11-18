from __future__ import annotations

from typing import List, Tuple

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.models.enums import Policy
from bot.services.github_store import GitHubFileStore
from bot.services.rules_file import parse_text, list_rules, describe_rule
from bot.metrics import INPUT_VALID

router = Router()


@router.message(Command("stats"))
async def stats_command(m: Message, store: GitHubFileStore) -> None:
    try:
        fetched = await store.fetch()
        lines = parse_text(fetched["text"])
        rules = list_rules(lines)
        from collections import Counter
        stats = Counter(r.type.value for _, r in rules)
        total = len(rules)
        lines_text = [f"📊 <b>Статистика правил</b>\n", f"📋 Всего: {total}\n"]
        for rtype, count in sorted(stats.items()):
            pct = count * 100 // total if total else 0
            lines_text.append(f"{rtype}: {count} ({pct}%)")
        await m.answer("\n".join(lines_text))
    except Exception:
        await m.answer("❌ Ошибка загрузки статистики")


@router.message(Command("recent"))
async def recent_command(m: Message, store: GitHubFileStore) -> None:
    try:
        commits = await store.get_recent_commits(limit=5)
        if not commits:
            await m.answer("💭 Нет последних изменений")
            return
        lines_text = ["🕒 <b>Последние изменения</b>\n"]
        for c in commits:
            msg = c.get("commit", {}).get("message", "").split("\n")[0][:50]
            author = c.get("commit", {}).get("author", {}).get("name", "Unknown")
            date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
            url = c.get("html_url", "")
            lines_text.append(f"• <code>{msg}</code>")
            lines_text.append(f"  {author} | {date}")
            if url:
                lines_text.append(f"  <a href='{url}'>Ссылка</a>")
            lines_text.append("")
        await m.answer("\n".join(lines_text))
    except Exception:
        await m.answer("❌ Ошибка загрузки истории")

PAGE_SIZE = 20


async def build_view_response(store: GitHubFileStore, policy: str | None = None, page: int = 0, rule_type: str | None = None, file_type: str = "PROXY"):
    file_path = store.get_path_for_policy(file_type)
    fetched = await store.fetch(file_path=file_path)
    lines = parse_text(fetched["text"])
    rules = list_rules(lines)
    filtered = _filter_rules(rules, None if policy in (None, "ALL") else policy)
    if rule_type and rule_type != "ALL":
        filtered = [r for r in filtered if r[1].type.value == rule_type]
    body, kb = _render_page(filtered, page, rule_type or "ALL", rules, file_type)
    return body, kb.as_markup()


def _filter_rules(rules: List[Tuple[int, object]], policy: str | None):
    if policy and policy in {p.value for p in Policy}:
        target = Policy(policy)
        return [r for r in rules if getattr(r[1], "policy", None) == target]
    return rules


def _render_page(filtered, page: int, rule_type: str, all_rules, file_type: str = "PROXY") -> tuple[str, InlineKeyboardBuilder]:
    from collections import Counter
    sorted_rules = sorted(filtered, key=lambda x: (x[1].value.lower(), x[1].type.value))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = sorted_rules[start:end]
    total = len(sorted_rules)

    stats = Counter(r.type.value for _, r in all_rules)
    stats_line = " | ".join(f"{k}: {v}" for k, v in sorted(stats.items()))
    
    lines = [f"📊 {stats_line}", f"📋 Показано: {total}", ""]
    for i, (_, rule) in enumerate(chunk, start=start + 1):
        lines.append(f"{i}. `{describe_rule(rule)}`")

    kb = InlineKeyboardBuilder()
    # File type selection
    proxy_text = "🚀 PROXY" if file_type == "PROXY" else "🚀 Proxy"
    direct_text = "⚡ DIRECT" if file_type == "DIRECT" else "⚡ Direct"
    kb.button(text=proxy_text, callback_data=f"view:file:PROXY:{rule_type}:page:{page}")
    kb.button(text=direct_text, callback_data=f"view:file:DIRECT:{rule_type}:page:{page}")
    kb.adjust(2)
    
    # Rule type selection
    kb.button(text="🌐 DOMAIN-SUFFIX", callback_data=f"view:type:DOMAIN-SUFFIX:file:{file_type}:page:0")
    kb.button(text="🎯 DOMAIN", callback_data=f"view:type:DOMAIN:file:{file_type}:page:0")
    kb.button(text="🔍 KEYWORD", callback_data=f"view:type:DOMAIN-KEYWORD:file:{file_type}:page:0")
    kb.button(text="🔢 IP-CIDR", callback_data=f"view:type:IP-CIDR:file:{file_type}:page:0")
    kb.button(text="📋 ВСЕ", callback_data=f"view:type:ALL:file:{file_type}:page:0")
    kb.adjust(2)
    
    nav = InlineKeyboardBuilder()
    if start > 0:
        nav.button(text=f"⬅️ {page}", callback_data=f"view:type:{rule_type}:file:{file_type}:page:{page-1}")
    if end < total:
        nav.button(text=f"➡️ {page+2}", callback_data=f"view:type:{rule_type}:file:{file_type}:page:{page+1}")
    if nav.buttons:
        kb.attach(nav)
    
    kb.button(text="💾 Скачать", callback_data=f"view:download:{file_type}")
    return "\n".join(lines) if total else "📋 Конфиг пуст\n\nДобавьте первое правило!", kb


@router.message(F.text.in_({"📋 Просмотр конфига", "Просмотр конфига"}))
@router.message(Command("view"))
async def view_config(m: Message, store: GitHubFileStore) -> None:
    try:
        body, markup = await build_view_response(store, policy="ALL", page=0, rule_type="ALL", file_type="PROXY")
    except Exception:
        await m.answer("❌ Не удалось получить конфиг из GitHub")
        return
    INPUT_VALID.labels(type="view").inc()
    await m.answer(body, reply_markup=markup, parse_mode="Markdown")


@router.callback_query(F.data.startswith("view:"))
async def on_view_pager(c: CallbackQuery, store: GitHubFileStore) -> None:
    parts = c.data.split(":")
    
    if parts[1] == "download":
        file_type = parts[2] if len(parts) > 2 else "PROXY"
        try:
            file_path = store.get_path_for_policy(file_type)
            fetched = await store.fetch(file_path=file_path)
            from aiogram.types import BufferedInputFile
            filename = f"shadowrocket_{file_type.lower()}.conf"
            file = BufferedInputFile(fetched["text"].encode(), filename=filename)
            await c.message.answer_document(file, caption=f"📥 Конфиг Shadowrocket ({file_type})")
            await c.answer("✅ Файл отправлен")
        except Exception:
            await c.answer("❌ Ошибка скачивания", show_alert=True)
        return
    
    # Parse new format: view:type:RULE_TYPE:file:FILE_TYPE:page:N or view:file:FILE_TYPE:RULE_TYPE:page:N
    rule_type = "ALL"
    file_type = "PROXY"
    page = 0
    
    if parts[1] == "type" and len(parts) >= 6:
        rule_type = parts[2]
        file_type = parts[4] if parts[3] == "file" else "PROXY"
        page = int(parts[6]) if len(parts) > 6 and parts[5] == "page" else 0
    elif parts[1] == "file" and len(parts) >= 4:
        file_type = parts[2]
        rule_type = parts[3]
        page = int(parts[5]) if len(parts) > 5 and parts[4] == "page" else 0

    try:
        body, markup = await build_view_response(store, policy="ALL", page=page, rule_type=rule_type, file_type=file_type)
    except Exception:
        await c.answer("❌ Ошибка загрузки", show_alert=True)
        return

    await c.message.edit_text(body, reply_markup=markup, parse_mode="Markdown")
    await c.answer()
