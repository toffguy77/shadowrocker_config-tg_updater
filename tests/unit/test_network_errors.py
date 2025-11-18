import datetime as dt
import pytest
from unittest.mock import MagicMock, AsyncMock
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.add_rule import on_enter_value, on_confirm, AddRule
from bot.services.github_store import GitHubFileStore


class FakeState:
    def __init__(self):
        self._data = {}
        self.state = None

    async def get_data(self):
        return dict(self._data)

    async def clear(self):
        self._data.clear()
        self.state = None

    async def set_state(self, s):
        self.state = s

    async def update_data(self, **kwargs):
        self._data.update(kwargs)


class StoreWithError(GitHubFileStore):
    def __init__(self):
        pass
    
    def get_path_for_policy(self, policy: str) -> str:
        return "rules/private.list"

    async def fetch(self, file_path: str = None):
        raise Exception("Network timeout")

    async def commit(self, *args, file_path=None, **kwargs):
        raise Exception("GitHub API error")


@pytest.mark.asyncio
async def test_add_rule_fetch_error(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"), text="example.com")
    sent = {"texts": []}

    async def m_answer(self, text, **kwargs):
        sent["texts"].append(text)
        mock_msg = MagicMock()
        mock_msg.edit_text = AsyncMock(side_effect=lambda t, **kw: sent["texts"].append(t))
        mock_msg.delete = AsyncMock()
        return mock_msg

    monkeypatch.setattr(Message, "answer", m_answer)

    state = FakeState()
    await state.update_data(rule_type="DOMAIN")
    await state.set_state(AddRule.entering_value)

    store = StoreWithError()
    await on_enter_value(m, state, store)

    assert any("Ошибка загрузки конфига" in t for t in sent["texts"])


@pytest.mark.asyncio
async def test_add_rule_commit_error(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    cuser = User(id=123, is_bot=False, first_name="U")
    cq = CallbackQuery(id="1", from_user=cuser, chat_instance="ci", data="add:confirm:add", message=m)

    sent = {"edited": []}

    async def m_edit(self, text, **kwargs):
        sent["edited"].append(text)

    monkeypatch.setattr(Message, "edit_text", m_edit)

    async def cq_answer(self, *args, **kwargs):
        return None

    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    state = FakeState()
    await state.update_data(rule_type="DOMAIN", value="example.com")

    store = StoreWithError()
    await on_confirm(cq, state, store)

    assert any("Ошибка" in t for t in sent["edited"])
