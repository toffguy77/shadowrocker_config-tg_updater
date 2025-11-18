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
    choosing_file = State()
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
    return result


@router.message(DeleteRule.entering_query)
async def on_delete_query(m: Message, state: FSMContext, store: GitHubFileStore) -> None:
    q = (m.text or "").strip()
    if not q:
        await m.answer("⚠️ Пустой запрос")
        return
    
    data = await state.get_data()
    file_type = data.get("file_type", "PROXY")
    
    loading_msg = await m.answer("⌛ Ищу...")
    try:
        file_path = store.get_path_for_policy(file_type)
        fetched = await store.fetch(file_path=file_path)
        rules_all = list_rules(parse_text(fetched["text"]))
        filtered = _filter_rules_by_query(rules_all, q)
        if loading_msg:
            await loading_msg.delete()
    except Exception:
        if loading_msg:
            await loading_msg.edit_text("❌ Ошибка загрузки")
        return
    if not filtered:
        await m.answer("🔍 Ничего не найдено")
        return
    await state.update_data(delete_filter=q)
    await state.set_state(DeleteRule.choosing_rule)

    body, btns, nav = _render_delete_page(filtered, page=0)
    kb = btns.as_markup()
    nav_markup = nav.as_markup()
    if getattr(nav_markup, "inline_keyboard", None):
        kb.inline_keyboard.append(nav_markup.inline_keyboard[0])
    await m.answer(body, reply_markup=kb, parse_mode="Markdown")


def _render_delete_page(rules, page: int):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    if not rules:
        return "Ничего не найдено", InlineKeyboardBuilder(), InlineKeyboardBuilder()
    
    sorted_rules = sorted(rules, key=lambda x: (x[1].value.lower(), x[1].type.value))
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = sorted_rules[start:end]
    total = len(sorted_rules)

    lines = ["Выберите правило для удаления:", ""]
    for i, (idx_in_file, rule) in enumerate(chunk, start=start + 1):
        lines.append(f"{i}. `{rule_line(rule)}`")
    
    builder = InlineKeyboardBuilder()
    for i, (idx_in_file, rule) in enumerate(chunk, start=start + 1):
        builder.button(text=f"❌ {i}", callback_data=f"del:pick:{idx_in_file}:{page}")
    builder.adjust(5)
    
    nav = InlineKeyboardBuilder()
    if start > 0:
        nav.button(text="⬅️", callback_data=f"del:page:{page-1}")
    if end < total:
        nav.button(text="➡️", callback_data=f"del:page:{page+1}")
    return "\n".join(lines), builder, nav


@router.message(F.text == "🗑️ Удалить правило")
async def delete_entrypoint(m: Message, state: FSMContext, store: GitHubFileStore) -> None:
    await state.clear()
    await state.set_state(DeleteRule.choosing_file)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 PROXY файл", callback_data="del:file:PROXY")
    kb.button(text="⚡ DIRECT файл", callback_data="del:file:DIRECT")
    kb.adjust(1)
    await m.answer("Выберите файл для удаления правила:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("del:file:"))
async def on_delete_file_select(c: CallbackQuery, state: FSMContext) -> None:
    _, _, file_type = c.data.split(":", 2)
    await state.update_data(file_type=file_type)
    await state.set_state(DeleteRule.entering_query)
    await c.message.edit_text(f"Пришлите URL/домен/ключевое слово или IP для поиска в {file_type} файле.\n\nОтмена: /cancel")
    await c.answer()


@router.callback_query(F.data.startswith("del:page:"))
async def on_del_page(c: CallbackQuery, state: FSMContext, store: GitHubFileStore) -> None:
    page = int(c.data.split(":")[-1])
    data = await state.get_data()
    q = (data.get("delete_filter") or "").strip()
    file_type = data.get("file_type", "PROXY")
    file_path = store.get_path_for_policy(file_type)
    fetched = await store.fetch(file_path=file_path)
    rules_all = list_rules(parse_text(fetched["text"]))
    rules = _filter_rules_by_query(rules_all, q)
    body, btns, nav = _render_delete_page(rules, page)
    kb = btns.as_markup()
    nav_markup = nav.as_markup()
    if getattr(nav_markup, "inline_keyboard", None):
        kb.inline_keyboard.append(nav_markup.inline_keyboard[0])
    await c.message.edit_text(body, reply_markup=kb, parse_mode="Markdown")
    await c.answer()


@router.callback_query(F.data.startswith("del:pick:"))
async def on_del_pick(c: CallbackQuery, state: FSMContext, store: GitHubFileStore) -> None:
    _, _, idx_str, page_str = c.data.split(":")
    idx_in_file = int(idx_str)

    data = await state.get_data()
    file_type = data.get("file_type", "PROXY")
    file_path = store.get_path_for_policy(file_type)
    fetched = await store.fetch(file_path=file_path)
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
    await state.update_data(delete_idx=i, preview=rule_line(rule))

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
    old_idx = int(data["delete_idx"])
    file_type = data.get("file_type", "PROXY")
    username = c.from_user.username if c.from_user else None

    try:
        file_path = store.get_path_for_policy(file_type)
        fetched = await store.fetch(file_path=file_path)
        lines = parse_text(fetched["text"])
    except Exception as e:
        await c.message.edit_text(f"❌ Ошибка загрузки конфига: {e}")
        await c.answer()
        return

    if old_idx >= len(lines) or lines[old_idx].kind != "rule" or not lines[old_idx].rule:
        await c.message.edit_text("Не удалось удалить: правило изменилось. Попробуйте снова.")
        await state.clear()
        await c.answer()
        return

    removed_cmnt = GitHubFileStore.removed_comment(username)
    new_lines = rf_delete_rule(lines, old_idx, removed_comment=removed_cmnt)
    new_text = render_lines(new_lines)
    try:
        resp = await store.commit(new_text, store.commit_message_delete(data.get("preview", "rule"), username), username, None, fetched["sha"], file_path=file_path)  # type: ignore[arg-type]
    except Exception as e:
        await c.message.edit_text(f"❌ Ошибка сохранения в GitHub: {e}")
        await c.answer()
        return
    from bot.metrics import RULES_DELETED
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    RULES_DELETED.inc()
    url = resp.get("commit", {}).get("html_url")
    kb = InlineKeyboardBuilder()
    if url:
        kb.button(text="🔗 Посмотреть коммит", url=url)
    await c.message.edit_text(f"✅ <b>Правило удалено</b>\n\n<code>{data.get('preview', '')}</code>", reply_markup=kb.as_markup() if kb.buttons else None)
    await state.clear()
    await c.answer("✅ Удалено!")
