import datetime as dt
import pytest
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.delete_rule import on_del_confirm, DeleteRule
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


class StoreWithChangedFile(GitHubFileStore):
    def __init__(self):
        pass
    
    def get_path_for_policy(self, policy: str) -> str:
        return "rules/private.list"

    async def fetch(self, file_path: str = None):
        # Return file where the rule at index 0 is now a comment
        return {"sha": "sha1", "text": "# This was a rule\nDOMAIN,other.com\n"}

    async def commit(self, *args, file_path=None, **kwargs):
        return {"commit": {"html_url": "https://example.com/commit/1"}}


@pytest.mark.asyncio
async def test_delete_rule_validates_line_type(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    cuser = User(id=123, is_bot=False, first_name="U")
    cq = CallbackQuery(id="1", from_user=cuser, chat_instance="ci", data="del:confirm:yes", message=m)

    sent = {"edited": []}

    async def m_edit(self, text, **kwargs):
        sent["edited"].append(text)

    monkeypatch.setattr(Message, "edit_text", m_edit)

    async def cq_answer(self, *args, **kwargs):
        return None

    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    state = FakeState()
    # User selected index 0, but it's now a comment
    await state.update_data(delete_idx=0, preview="DOMAIN,example.com")
    await state.set_state(DeleteRule.confirming)

    store = StoreWithChangedFile()
    await on_del_confirm(cq, state, store)

    # Should detect that the line is no longer a rule
    assert any("изменилось" in t or "Не удалось" in t for t in sent["edited"])
    assert state._data == {}  # State should be cleared
