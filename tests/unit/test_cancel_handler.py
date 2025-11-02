"""Test global cancel handler."""
import datetime as dt
import pytest
from aiogram.types import Message, Chat, User
from aiogram.fsm.context import FSMContext

from bot.handlers.cancel import cancel_handler
from bot.handlers.add_rule import AddRule


class FakeState:
    def __init__(self, initial_state=None):
        self._state = initial_state
        self._data = {}
        self.cleared = False

    async def get_state(self):
        return self._state

    async def clear(self):
        self.cleared = True
        self._state = None
        self._data.clear()

    async def set_state(self, s):
        self._state = s

    async def get_data(self):
        return dict(self._data)


@pytest.mark.asyncio
async def test_cancel_with_no_state(monkeypatch):
    """Test /cancel when no FSM state is active."""
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    
    sent = []
    async def m_answer(self, text, **kwargs):
        sent.append(text)
    monkeypatch.setattr(Message, "answer", m_answer)
    
    state = FakeState(initial_state=None)
    await cancel_handler(m, state)
    
    assert any("Нечего отменять" in t for t in sent)
    assert not state.cleared


@pytest.mark.asyncio
async def test_cancel_with_active_state(monkeypatch):
    """Test /cancel when FSM state is active."""
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    
    sent = []
    async def m_answer(self, text, **kwargs):
        sent.append(text)
    monkeypatch.setattr(Message, "answer", m_answer)
    
    state = FakeState(initial_state=AddRule.entering_value)
    await cancel_handler(m, state)
    
    assert any("Операция отменена" in t for t in sent)
    assert state.cleared


@pytest.mark.asyncio
async def test_cancel_clears_state_data(monkeypatch):
    """Test that /cancel clears all state data."""
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    
    sent = []
    async def m_answer(self, text, **kwargs):
        sent.append(text)
    monkeypatch.setattr(Message, "answer", m_answer)
    
    state = FakeState(initial_state=AddRule.confirming)
    state._data = {"rule_type": "DOMAIN", "value": "example.com"}
    
    await cancel_handler(m, state)
    
    assert state.cleared
    assert len(state._data) == 0
