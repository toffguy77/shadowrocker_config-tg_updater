"""Tests for add rule flow with policy selection."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import datetime as dt

from aiogram.types import Message, CallbackQuery, Chat, User
from aiogram.fsm.context import FSMContext

from bot.handlers.add_rule import on_enter_value, on_confirm
from bot.models.enums import Policy


class FakeState:
    def __init__(self, data=None):
        self._data = data or {}
        self.cleared = False
    
    async def get_data(self):
        return self._data
    
    async def update_data(self, **kwargs):
        self._data.update(kwargs)
    
    async def set_state(self, state):
        pass
    
    async def clear(self):
        self.cleared = True
        self._data = {}


class MockStoreWithPolicy:
    def __init__(self, text="", sha="abc123"):
        self.text = text
        self.sha = sha
        self.path_proxy = "rules/private.list"
        self.path_direct = "rules/private.direct.list"
    
    def get_path_for_policy(self, policy: str) -> str:
        if policy == Policy.DIRECT.value:
            return self.path_direct
        return self.path_proxy
    
    async def fetch(self, file_path: str = None):
        return {"text": self.text, "sha": self.sha}
    
    async def commit(self, new_text: str, message: str, author_name: str | None, 
                    author_email: str | None, base_sha: str, file_path: str = None):
        return {"commit": {"html_url": "https://github.com/test/commit/123"}}
    
    @staticmethod
    def commit_message_add(rule_line: str, username: str | None) -> str:
        u = f" by @{username}" if username else ""
        return f"Add rule: {rule_line}{u}"
    
    @staticmethod
    def added_comment(username: str | None, now=None) -> str:
        uname = f"@{username}" if username else "unknown"
        return f"# Added: 2024-01-01 00:00:00 UTC | User: {uname}"


@pytest.mark.asyncio
async def test_add_rule_with_policy_success(monkeypatch):
    """Test successful add rule flow with policy selection."""
    store = MockStoreWithPolicy()
    state = FakeState({
        "rule_type": "DOMAIN",
        "policy": "PROXY",
        "value": "example.com"
    })
    
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        text="example.com"
    )
    
    sent = []
    async def m_answer(self, text, **kwargs):
        sent.append(text)
        mock_msg = MagicMock()
        mock_msg.delete = AsyncMock()
        return mock_msg
    
    monkeypatch.setattr(Message, "answer", m_answer)
    
    await on_enter_value(m, state, store)
    
    # Should show preview with rule
    assert any("Правило:" in t for t in sent)


@pytest.mark.asyncio
async def test_add_rule_missing_policy(monkeypatch):
    """Test that missing policy is handled gracefully."""
    store = MockStoreWithPolicy()
    state = FakeState({"rule_type": "DOMAIN"})  # Missing policy
    
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        text="example.com"
    )
    
    sent = []
    async def m_answer(self, text, **kwargs):
        sent.append(text)
        return MagicMock()
    
    monkeypatch.setattr(Message, "answer", m_answer)
    
    await on_enter_value(m, state, store)
    
    # Should show error about missing policy
    assert any("политику" in t for t in sent)


@pytest.mark.asyncio
async def test_confirm_add_with_policy(monkeypatch):
    """Test confirm add with policy data."""
    store = MockStoreWithPolicy()
    state = FakeState({
        "rule_type": "DOMAIN",
        "policy": "DIRECT",
        "value": "example.com"
    })
    
    cuser = User(id=123, is_bot=False, first_name="U")
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    cq = CallbackQuery(id="1", from_user=cuser, chat_instance="ci", data="add:confirm:add", message=m)
    
    sent = []
    async def m_edit(self, text, **kwargs):
        sent.append(text)
    
    async def cq_answer(self, *args, **kwargs):
        pass
    
    monkeypatch.setattr(Message, "edit_text", m_edit)
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)
    
    await on_confirm(cq, state, store)
    
    # Should show success message
    assert any("Правило добавлено" in t for t in sent)
    assert state.cleared