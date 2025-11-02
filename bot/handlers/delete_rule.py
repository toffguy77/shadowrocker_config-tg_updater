from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

import ipaddress
from urllib.parse import urlparse

from bot.models.enums import Policy, RuleType
from bot.services.github_store import GitHubFileStore
from bot.services.rules_file import parse_text, list_rules, delete_rule as rf_delete_rule, render_lines, rule_line
from bot.validators.domain import normalize_domain_exact, normalize_domain_suffix

router = Router()

PAGE_SIZE = 20


class DeleteRule(StatesGroup):
    entering_query = State()
    choosing_rule = State()
    confirming = State()


def _extract_tokens(query: str) -> list[str]:
    q = (query or "").strip().lower()
    if not q:
        return []
    tokens = [q]
    # try URL/host
    try:
        p = urlparse(query)
        host = p.netloc or p.path
        host = host.strip().strip(".")
        ok, host_norm_or_err = normalize_domain_exact(host)
        if ok:
            tokens.append(host_norm_or_err.lower())
            ok2, base_or_err = normalize_domain_suffix(host)
            if ok2:
                tokens.append(base_or_err.lower())
    except Exception:
        pass
    return list(dict.fromkeys([t for t in tokens if t]))


def _filter_rules_by_query(rules, query: str):
    tokens = _extract_tokens(query)
    ip = None
    try:
        ip = ipaddress.ip_address(query.strip())
    except Exception:
        ip = None

    result = []
    for idx, rule in rules:
        val = rule.value.lower()
        matched = any(t in val for t in tokens)
        if not matched and ip and rule.type.value == "IP-CIDR":
            try:
                net = ipaddress.ip_network(rule.value, strict=False)
                if ip in net:
                    matched = True
            except Exception:
                pass
        if matched:
            result.append((idx, rule))
    # sort like view
    result.sort(key=lambda x: (x[1].value.lower(), x[1].type.value))
    return result


@router.message(DeleteRule.entering_query)
async def on_delete_query(m: Message, state: FSMContext, store: GitHubFileStore) -> None:
    q = (m.text or "").strip()
    if not q:
        await m.answer("Пустой запрос. Пришлите URL/домен/ключевое слово или IP.")
        return
    fetched = await store.fetch()
    rules_all = list_rules(parse_text(fetched["text"]))
    filtered = _filter_rules_by_query(rules_all, q)
    if not filtered:
        await m.answer("Ничего не найдено по запросу.")
        return
    await state.update_data(delete_filter=q)
    await state.set_state(DeleteRule.choosing_rule)

    body, btns, nav = _render_delete_page(filtered, page=0)
    kb = btns.as_markup()
    nav_markup = nav.as_markup()
    if getattr(nav_markup, "inline_keyboard", None):
        kb.inline_keyboard.append(nav_markup.inline_keyboard[0])
    await m.answer(body, reply_markup=kb)


def _render_delete_page(rules, page: int):
    # Sort alphabetically by rule value (case-insensitive), then by type
    sorted_rules = sorted(rules, key=lambda x: (x[1].value.lower(), x[1].type.value))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = sorted_rules[start:end]
    total = len(sorted_rules)

    lines = ["Выберите правило для удаления:", ""]
    kb = []
    for i, (idx_in_file, rule) in enumerate(chunk, start=start + 1):
        lines.append(f"{i}. ❌ {rule_line(rule)}")
    # Build buttons
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for i, (idx_in_file, rule) in enumerate(chunk, start=start):
        builder.button(text=f"❌ #{i+1}", callback_data=f"del:pick:{idx_in_file}:{page}")
    builder.adjust(2)
    nav = InlineKeyboardBuilder()
    if start > 0:
        nav.button(text="⬅️", callback_data=f"del:page:{page-1}")
    if end < total:
        nav.button(text="➡️", callback_data=f"del:page:{page+1}")
    return "\n".join(lines), builder, nav


@router.message(F.text == "🗑️ Удалить правило")
async def delete_entrypoint(m: Message, state: FSMContext, store: GitHubFileStore) -> None:
    await state.clear()
    await state.set_state(DeleteRule.entering_query)
    await m.answer("Пришлите URL/домен/ключевое слово или IP для поиска.\n\nОтмена: /cancel")


@router.callback_query(F.data.startswith("del:page:"))
async def on_del_page(c: CallbackQuery, state: FSMContext, store: GitHubFileStore) -> None:
    page = int(c.data.split(":")[-1])
    data = await state.get_data()
    q = (data.get("delete_filter") or "").strip()
    fetched = await store.fetch()
    rules_all = list_rules(parse_text(fetched["text"]))
    rules = _filter_rules_by_query(rules_all, q)
    body, btns, nav = _render_delete_page(rules, page)
    kb = btns.as_markup()
    nav_markup = nav.as_markup()
    if getattr(nav_markup, "inline_keyboard", None):
        kb.inline_keyboard.append(nav_markup.inline_keyboard[0])
    await c.message.edit_text(body, reply_markup=kb)
    await c.answer()


@router.callback_query(F.data.startswith("del:pick:"))
async def on_del_pick(c: CallbackQuery, state: FSMContext, store: GitHubFileStore) -> None:
    _, _, idx_str, page_str = c.data.split(":")
    idx_in_file = int(idx_str)

    fetched = await store.fetch()
    lines = parse_text(fetched["text"])

    rules = list_rules(lines)
    # idx_in_file refers to original file indices, so direct match
    match = next(((i, r) for i, r in rules if i == idx_in_file), None)
    if not match:
        await c.message.edit_text("Правило не найдено (возможно, изменилось). Обновите список.")
        await c.answer()
        return
    i, rule = match
    await state.set_state(DeleteRule.confirming)
    await state.update_data(delete_idx=i, preview=rule_line(rule), sha=fetched["sha"])

    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Удалить", callback_data="del:confirm:yes")
    kb.button(text="❌ Отменить", callback_data="del:confirm:no")
    kb.adjust(2)
    await c.message.edit_text(
        f"Удалить правило?\n\n{rule_line(rule)}\n\n⚠️ Действие необратимо",
        reply_markup=kb.as_markup(),
    )
    await c.answer()


@router.callback_query(F.data.startswith("del:confirm:"))
async def on_del_confirm(c: CallbackQuery, state: FSMContext, store: GitHubFileStore) -> None:
    action = c.data.split(":")[-1]
    if action == "no":
        await state.clear()
        await c.message.edit_text("Отменено.")
        await c.answer()
        return

    data = await state.get_data()
    idx = int(data["delete_idx"])
    username = c.from_user.username if c.from_user else None

    fetched = await store.fetch()
    lines = parse_text(fetched["text"])

    if idx >= len(lines):
        await c.message.edit_text("Не удалось удалить: список изменился. Попробуйте снова.")
        await state.clear()
        await c.answer()
        return

    removed_cmnt = GitHubFileStore.removed_comment(username)
    new_lines = rf_delete_rule(lines, idx, removed_comment=removed_cmnt)
    new_text = render_lines(new_lines)
    resp = await store.commit(new_text, store.commit_message_delete(data.get("preview", "rule"), username), username, None, fetched["sha"])  # type: ignore[arg-type]
    from bot.metrics import RULES_DELETED
    RULES_DELETED.inc()
    url = resp.get("commit", {}).get("html_url")
    await c.message.edit_text(f"✅ Правило удалено\n\n{data.get('preview', '')}\n\n{('Коммит: ' + url) if url else ''}")
    await state.clear()
    await c.answer()
