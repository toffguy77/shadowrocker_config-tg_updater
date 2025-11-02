import datetime as dt
import pytest
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.add_rule import add_entrypoint, on_choose_type, on_enter_value, on_confirm, AddRule
from bot.services.github_store import GitHubFileStore


class FakeState:
    def __init__(self):
        self._data = {}
        self.cleared = False
        self.state = None

    async def get_data(self):
        return dict(self._data)

    async def clear(self):
        self.cleared = True
        self._data.clear()
        self.state = None

    async def set_state(self, s):
        self.state = s

    async def update_data(self, **kwargs):
        self._data.update(kwargs)


class StoreNew(GitHubFileStore):
    def __init__(self):
        pass

    async def fetch(self):
        return {"sha": "sha0", "text": "# header\n"}

    async def commit(self, *args, **kwargs):
        return {"commit": {"html_url": "https://example.com/commit/1"}}


class StoreExisting(GitHubFileStore):
    def __init__(self):
        pass

    async def fetch(self):
        # existing with third column to verify policy removal path
        return {"sha": "sha1", "text": "DOMAIN,example.com,PROXY\n"}

    async def commit(self, *args, **kwargs):
        return {"commit": {"html_url": "https://example.com/commit/2"}}


@pytest.mark.asyncio
async def test_add_rule_new_flow(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    cuser = User(id=123, is_bot=False, first_name="U")
    cq = CallbackQuery(id="1", from_user=cuser, chat_instance="ci", data="add:type:DOMAIN", message=m)

    sent = {"texts": [], "edited": []}

    async def m_answer(self, text, **kwargs):
        sent["texts"].append(text)

    async def m_edit(self, text, **kwargs):
        sent["edited"].append(text)

    monkeypatch.setattr(Message, "answer", m_answer)
    monkeypatch.setattr(Message, "edit_text", m_edit)

    async def cq_answer(self, *args, **kwargs):
        return None
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    state = FakeState()

    await add_entrypoint(m, state)
    await on_choose_type(cq, state)

    store = StoreNew()
    m2 = Message(message_id=2, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"), text="example.com")
    await on_enter_value(m2, state, store)

    assert any("Правило:" in t for t in sent["texts"])  # preview shown

    cq2 = CallbackQuery(id="2", from_user=cuser, chat_instance="ci", data="add:confirm:add", message=m)
    await on_confirm(cq2, state, store)

    assert any("✅ Правило добавлено" in t for t in sent["edited"])  # final message


@pytest.mark.asyncio
async def test_add_rule_replace_existing(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    cuser = User(id=123, is_bot=False, first_name="U")
    cq = CallbackQuery(id="1", from_user=cuser, chat_instance="ci", data="add:type:DOMAIN", message=m)

    sent = {"edited": []}

    async def m_edit(self, text, **kwargs):
        sent["edited"].append(text)

    async def m_answer(self, text, **kwargs):
        # used by on_enter_value when conflict
        sent["edited"].append(text)

    monkeypatch.setattr(Message, "edit_text", m_edit)
    monkeypatch.setattr(Message, "answer", m_answer)

    async def cq_answer(self, *args, **kwargs):
        return None
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    state = FakeState()
    await on_choose_type(cq, state)

    store = StoreExisting()
    m2 = Message(message_id=2, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"), text="example.com")
    await on_enter_value(m2, state, store)

    # Verify sha is NOT stored in state (race condition fix)
    data = await state.get_data()
    assert "sha" not in data
    # Verify existing_idx IS stored for existing rules
    assert "existing_idx" in data
    assert data["existing_idx"] == 0

    # Now confirm replace
    cq2 = CallbackQuery(id="2", from_user=cuser, chat_instance="ci", data="add:confirm:replace", message=m)
    await on_confirm(cq2, state, store)
    assert any("✅ Правило сохранено" in t for t in sent["edited"])