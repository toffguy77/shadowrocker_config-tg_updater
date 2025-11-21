import datetime as dt
import pytest
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.delete_rule import delete_entrypoint, on_del_pick, on_del_confirm, DeleteRule
from bot.services.github_store import GitHubFileStore


class FakeState:
    def __init__(self):
        self._data = {}
        self.state = None
        self.cleared = False

    async def get_data(self):
        return dict(self._data)

    async def set_state(self, s):
        self.state = s

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self.cleared = True
        self._data.clear()
        self.state = None


class StoreDel(GitHubFileStore):
    def __init__(self, text):
        self._text = text
        self.path_proxy = "rules/private.list"
        self.path_direct = "rules/private.direct.list"

    async def fetch(self, file_path: str = None, retry: int = 2):
        return {"sha": "sha0", "text": self._text}

    async def commit(self, *args, file_path=None, **kwargs):
        return {"commit": {"html_url": "https://example.com/commit/d"}}


@pytest.mark.asyncio
async def test_delete_rule_yes(monkeypatch):
    text = "DOMAIN,foo.com\nDOMAIN,bar.com\n"
    store = StoreDel(text)
    state = FakeState()

    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    sent = {"edited": [], "answered": []}

    async def m_answer(self, text, **kwargs):
        sent["answered"].append(text)

    async def c_edit(self, text, **kwargs):
        sent["edited"].append(text)

    monkeypatch.setattr(Message, "answer", m_answer)
    monkeypatch.setattr(Message, "edit_text", c_edit)

    async def cq_answer(self, *args, **kwargs):
        return None
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    # entrypoint shows file selection
    await delete_entrypoint(m, state, store)
    
    # Set file_type in state (simulating file selection)
    await state.update_data(file_type="PROXY")

    # pick first rule (idx=0), page=0
    cuser = User(id=123, is_bot=False, first_name="U")
    cq = CallbackQuery(id="1", from_user=cuser, chat_instance="ci", data="del:pick:0:0", message=m)
    await on_del_pick(cq, state, store)
    
    # Verify sha is NOT stored in state (race condition fix)
    data = await state.get_data()
    assert "sha" not in data

    # confirm deletion
    cq2 = CallbackQuery(id="2", from_user=cuser, chat_instance="ci", data="del:confirm:yes", message=m)
    await on_del_confirm(cq2, state, store)

    assert any("✅" in t and "удалено" in t for t in sent["edited"])