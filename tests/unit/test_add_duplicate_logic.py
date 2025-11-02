import datetime as dt
import pytest
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.add_rule import on_enter_value, on_confirm, AddRule
from bot.services.github_store import GitHubFileStore


class FakeState:
    def __init__(self):
        self._data = {}
        self.state = None

    async def get_data(self):
        return dict(self._data)

    async def set_state(self, s):
        self.state = s

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self._data.clear()
        self.state = None


class StoreWithoutPolicy(GitHubFileStore):
    """Store with existing rule without policy."""
    def __init__(self):
        pass

    async def fetch(self):
        return {"sha": "sha1", "text": "DOMAIN,example.com\n"}

    async def commit(self, *args, **kwargs):
        return {"commit": {"html_url": "https://example.com/commit/1"}}


@pytest.mark.asyncio
async def test_add_duplicate_without_policy_shows_keep(monkeypatch):
    """Test that adding duplicate rule without policy shows 'keep' option."""
    store = StoreWithoutPolicy()
    state = FakeState()
    state._data = {"rule_type": "DOMAIN"}
    
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        text="example.com"
    )
    
    sent = []
    
    async def m_answer(self, text, **kwargs):
        sent.append(text)
    
    monkeypatch.setattr(Message, "answer", m_answer)
    
    await on_enter_value(m, state, store)
    
    # Should show warning about existing rule
    assert any("⚠️ Правило уже существует" in t for t in sent)
    
    # Verify existing_idx is stored
    data = await state.get_data()
    assert "existing_idx" in data
    assert data["existing_idx"] == 0


@pytest.mark.asyncio
async def test_add_confirm_with_existing_no_policy_shows_keep(monkeypatch):
    """Test that confirming add when rule exists without policy shows keep option."""
    store = StoreWithoutPolicy()
    state = FakeState()
    state._data = {"rule_type": "DOMAIN", "value": "example.com"}
    
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
    
    # Should show option to keep existing
    assert any("⚠️ Правило уже существует" in t for t in sent)
    assert any("Оставить старое?" in t for t in sent)


@pytest.mark.asyncio
async def test_state_cleared_on_github_error(monkeypatch):
    """Test that state is cleared when GitHub fetch fails."""
    class FailStore(GitHubFileStore):
        def __init__(self):
            pass
        async def fetch(self):
            raise Exception("Network error")
    
    store = FailStore()
    state = FakeState()
    state._data = {"rule_type": "DOMAIN"}
    
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        text="example.com"
    )
    
    sent = []
    
    async def m_answer(self, text, **kwargs):
        sent.append(text)
    
    monkeypatch.setattr(Message, "answer", m_answer)
    
    await on_enter_value(m, state, store)
    
    # State should be cleared
    assert state._data == {}
    assert any("❌ Ошибка загрузки конфига" in t for t in sent)
