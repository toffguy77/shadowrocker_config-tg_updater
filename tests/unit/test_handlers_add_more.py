import datetime as dt
import pytest
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.add_rule import on_confirm
from bot.services.github_store import GitHubFileStore


class FakeState:
    def __init__(self, data):
        self._data = dict(data)
        self.cleared = False

    async def get_data(self):
        return dict(self._data)

    async def clear(self):
        self.cleared = True

    async def update_data(self, **kwargs):
        self._data.update(kwargs)


class StoreExisting(GitHubFileStore):
    def __init__(self, text):
        self._text = text

    async def fetch(self):
        return {"sha": "sha1", "text": self._text}

    async def commit(self, *args, **kwargs):
        return {"commit": {"html_url": "https://example.com/commit/x"}}


@pytest.mark.asyncio
async def test_add_keep_and_cancel(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    user = User(id=1, is_bot=False, first_name="U")

    edited = []
    async def edit(self, text, **kwargs):
        edited.append(text)
    async def cq_answer(self, *a, **k):
        return None

    monkeypatch.setattr(Message, "edit_text", edit)
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    # keep
    cq_keep = CallbackQuery(id="1", from_user=user, chat_instance="ci", data="add:confirm:keep", message=m)
    state = FakeState({"rule_type": "DOMAIN", "value": "a.com"})
    store = StoreExisting("DOMAIN,a.com\n")
    await on_confirm(cq_keep, state, store)
    assert any("Оставили" in t for t in edited) and state.cleared

    # cancel
    cq_cancel = CallbackQuery(id="2", from_user=user, chat_instance="ci", data="add:confirm:cancel", message=m)
    state2 = FakeState({"rule_type": "DOMAIN", "value": "a.com"})
    edited.clear()
    await on_confirm(cq_cancel, state2, store)
    assert any("Отменено" in t for t in edited) and state2.cleared


@pytest.mark.asyncio
async def test_add_add_conflict_branch(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    user = User(id=1, is_bot=False, first_name="U")

    edited = []
    async def edit(self, text, **kwargs):
        edited.append(text)
    async def cq_answer(self, *a, **k):
        return None

    monkeypatch.setattr(Message, "edit_text", edit)
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    # When rule already exists, 'add' branch should fall back to conflict flow
    cq_add = CallbackQuery(id="1", from_user=user, chat_instance="ci", data="add:confirm:add", message=m)
    state = FakeState({"rule_type": "DOMAIN", "value": "a.com"})
    store = StoreExisting("DOMAIN,a.com\n")
    await on_confirm(cq_add, state, store)
    assert any("Конфликт" in t or "уже существует" in t for t in edited)
