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

PAGE_SIZE = 20


async def build_view_response(store: GitHubFileStore, policy: str | None = None, page: int = 0):
    fetched = await store.fetch()
    lines = parse_text(fetched["text"])
    rules = list_rules(lines)
    filtered = _filter_rules(rules, None if policy in (None, "ALL") else policy)
    body, kb = _render_page(filtered, page)
    return body, kb.as_markup()


def _filter_rules(rules: List[Tuple[int, object]], policy: str | None):
    if policy and policy in {p.value for p in Policy}:
        target = Policy(policy)
        return [r for r in rules if getattr(r[1], "policy", None) == target]
    return rules


def _render_page(filtered, page: int) -> tuple[str, InlineKeyboardBuilder]:
    # Sort alphabetically by rule value (case-insensitive), then by type
    sorted_rules = sorted(filtered, key=lambda x: (x[1].value.lower(), x[1].type.value))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = sorted_rules[start:end]
    total = len(sorted_rules)

    lines = [f"📋 Всего правил: {total}", ""]
    for i, (_, rule) in enumerate(chunk, start=start + 1):
        lines.append(f"{i}. {describe_rule(rule)}")

    kb = InlineKeyboardBuilder()
    if start > 0:
        kb.button(text="⬅️", callback_data=f"view:ALL:page:{page-1}")
    if end < total:
        kb.button(text="➡️", callback_data=f"view:ALL:page:{page+1}")
    return "\n".join(lines) if total else "📋 Конфиг пуст\n\nДобавьте первое правило!", kb


@router.message(F.text.in_({"📋 Просмотр конфига", "Просмотр конфига"}))
@router.message(Command("view"))
async def view_config(m: Message, store: GitHubFileStore) -> None:
    try:
        body, markup = await build_view_response(store, policy="ALL", page=0)
    except Exception:
        await m.answer("❌ Не удалось получить конфиг из GitHub. Проверьте токен и доступы.")
        return
    INPUT_VALID.inc()
    await m.answer(body, reply_markup=markup)


@router.callback_query(F.data.startswith("view:"))
async def on_view_pager(c: CallbackQuery, store: GitHubFileStore) -> None:
    # format: view:ALL:page:1
    parts = c.data.split(":")
    policy = parts[1] if len(parts) > 1 else "ALL"
    page = int(parts[3]) if len(parts) > 3 and parts[2] == "page" else 0

    try:
        body, markup = await build_view_response(store, policy=policy, page=page)
    except Exception:
        await c.answer("Не удалось обновить список из GitHub", show_alert=True)
        return

    await c.message.edit_text(body, reply_markup=markup)
    await c.answer()
