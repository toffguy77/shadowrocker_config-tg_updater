from __future__ import annotations

import datetime as dt
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.rule_type import rule_type_kb
from bot.keyboards.confirm import confirm_add_kb, confirm_replace_kb
from bot.models.enums import RuleType
from bot.services.github_store import GitHubFileStore
from bot.services.rules_file import (
    parse_text,
    list_rules,
    find_rule_index,
    add_rule as rf_add_rule,
    clear_policy as rf_clear_policy,
    rule_line,
    Rule as RFRule,
    render_lines,
)
from bot.validators.domain import normalize_domain_exact, normalize_domain_suffix
from bot.validators.ip import normalize_ip
from bot.validators.keyword import normalize_keyword

router = Router()


class AddRule(StatesGroup):
    choosing_type = State()
    entering_value = State()
    confirming = State()


@router.message(Command("cancel"))
async def cancel_any(m: Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer("Отменено.")


@router.message(F.text == "➕ Добавить правило")
async def add_entrypoint(m: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddRule.choosing_type)
    await m.answer("Выберите тип правила:", reply_markup=rule_type_kb().as_markup())


@router.callback_query(F.data.startswith("add:type:"))
async def on_choose_type(c: CallbackQuery, state: FSMContext) -> None:
    _, _, raw_type = c.data.split(":", 2)
    await state.update_data(rule_type=raw_type)
    await state.set_state(AddRule.entering_value)
    if raw_type == RuleType.IP_CIDR.value:
        text = (
            "Введите IP-адрес или диапазон (например: 192.168.1.1 или 10.0.0.0/8).\n\nОтмена: /cancel"
        )
    elif raw_type == RuleType.DOMAIN_KEYWORD.value:
        text = (
            "Введите ключевое слово (например: google).\nБудет искаться в любой части домена.\n\nОтмена: /cancel"
        )
    else:
        text = (
            "Введите домен (например: google.com). Можно прислать URL — я извлеку домен.\n\nОтмена: /cancel"
        )
    await c.message.edit_text(text)
    await c.answer()


@router.message(AddRule.entering_value)
async def on_enter_value(m: Message, state: FSMContext, store: GitHubFileStore) -> None:
    # Handle cancel inline in this state
    txt = (m.text or "").strip()
    if txt.startswith("/cancel"):
        await state.clear()
        await m.answer("Отменено.")
        return

    data = await state.get_data()
    raw_type = data.get("rule_type")
    if not raw_type:
        await m.answer("Сначала выберите тип правила.")
        return

    value_raw = (m.text or "").strip()
    ok = False
    norm_value = ""
    error = ""
    if raw_type == RuleType.DOMAIN_SUFFIX.value:
        ok, res = normalize_domain_suffix(value_raw)
        norm_value = res if ok else ""
        error = res if not ok else ""
    elif raw_type == RuleType.DOMAIN.value:
        ok, res = normalize_domain_exact(value_raw)
        norm_value = res if ok else ""
        error = res if not ok else ""
    elif raw_type == RuleType.DOMAIN_KEYWORD.value:
        ok, res = normalize_keyword(value_raw)
        norm_value = res if ok else ""
        error = res if not ok else ""
    elif raw_type == RuleType.IP_CIDR.value:
        ok, res = normalize_ip(value_raw)
        norm_value = res if ok else ""
        error = res if not ok else ""
    else:
        error = "Неизвестный тип правила."

    if not ok:
        from bot.metrics import INPUT_INVALID
        INPUT_INVALID.inc()
        await m.answer(f"❌ Ошибка ввода\n\n{error}\n\nПопробуйте ещё раз или /cancel")
        return

    from bot.metrics import INPUT_VALID
    INPUT_VALID.inc()

    await state.update_data(value=norm_value)
    await state.set_state(AddRule.confirming)

    # Build preview and detect duplicates immediately
    rtype = RuleType(raw_type)
    value = norm_value

    fetched = await store.fetch()
    lines = parse_text(fetched["text"])
    idx = find_rule_index(lines, rtype, value)

    rule = RFRule(type=rtype, value=value, policy=None)
    preview = (
        f"Тип: {rtype.value}\nЗначение: {value}\n\nПравило:\n{rule_line(rule)}"
    )

    if idx is None:
        await m.answer(preview, reply_markup=confirm_add_kb().as_markup())
    else:
        existing = lines[idx].rule
        # If existing has a policy (third column), offer to strip it (replace)
        if existing and existing.policy is not None:
            await m.answer(
                f"⚠️ Правило уже существует с политикой\n\nСтарое: {rule_line(existing)}\nНовое: {rule_line(rule)}\n\nЗаменить (убрать политику)?",
                reply_markup=confirm_replace_kb().as_markup(),
            )
            await state.update_data(existing_idx=idx, conflict=True, sha=fetched["sha"]) 
        else:
            await m.answer(
                f"⚠️ Правило уже существует\n\n{rule_line(rule)}\n\nОставить старое или отменить?",
                reply_markup=confirm_replace_kb().as_markup(),
            )
            await state.update_data(existing_idx=idx, conflict=False, sha=fetched["sha"]) 


@router.callback_query(F.data.in_({"add:confirm:add", "add:confirm:replace", "add:confirm:keep", "add:confirm:cancel"}))
async def on_confirm(c: CallbackQuery, state: FSMContext, store: GitHubFileStore) -> None:
    action = c.data.split(":")[-1]
    if action == "cancel":
        await state.clear()
        await c.message.edit_text("Отменено.")
        await c.answer()
        return

    data = await state.get_data()
    rtype = RuleType(data["rule_type"])  # type: ignore[arg-type]
    value = data["value"]

    username = c.from_user.username if c.from_user else None

    # Re-fetch and re-evaluate to avoid races
    fetched = await store.fetch()
    lines = parse_text(fetched["text"])
    idx = find_rule_index(lines, rtype, value)

    rule = RFRule(type=rtype, value=value, policy=None)

    if action == "add":
        if idx is not None:
            # already exists now; fall back to conflict flow
            existing = lines[idx].rule
            await c.message.edit_text(
                f"⚠️ Правило уже существует\n\nСтарое: {rule_line(existing)}\nНовое: {rule_line(rule)}\n\nЗаменить?",
                reply_markup=confirm_replace_kb().as_markup(),
            )
            await state.update_data(existing_idx=idx, conflict=True)
            await c.answer()
            return
        cmnt = GitHubFileStore.added_comment(username)
        new_lines = rf_add_rule(lines, rule, cmnt)
        new_text = render_lines(new_lines)
        resp = await store.commit(new_text, store.commit_message_add(rule_line(rule), username), username, None, fetched["sha"])  # author_email optional
        from bot.metrics import RULES_ADDED
        RULES_ADDED.inc()
        url = resp.get("commit", {}).get("html_url")
        await c.message.edit_text(
            f"✅ Правило добавлено\n\n{rule_line(rule)}\n\n{('Коммит: ' + url) if url else ''}"
        )
        await state.clear()
        await c.answer()
        return

    if action == "keep":
        await state.clear()
        await c.message.edit_text("Оставили существующее правило без изменений.")
        await c.answer()
        return

    if action == "replace":
        if idx is None:
            # was deleted meanwhile; add as new
            cmnt = GitHubFileStore.added_comment(username)
            new_lines = rf_add_rule(lines, rule, cmnt)
        else:
            # strip third column (policy) if present
            new_lines = rf_clear_policy(lines, idx)
        new_text = render_lines(new_lines)
        resp = await store.commit(new_text, store.commit_message_add(rule_line(rule), username), username, None, fetched["sha"])  # reuse add message
        from bot.metrics import RULES_REPLACED
        RULES_REPLACED.inc()
        url = resp.get("commit", {}).get("html_url")
        await c.message.edit_text(
            f"✅ Правило сохранено\n\n{rule_line(rule)}\n\n{('Коммит: ' + url) if url else ''}"
        )
        await state.clear()
        await c.answer()
