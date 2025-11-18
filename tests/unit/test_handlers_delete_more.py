import datetime as dt
import pytest
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.delete_rule import on_del_confirm, on_del_page
from bot.services.github_store import GitHubFileStore


class FakeState:
    def __init__(self, data):
        self._data = dict(data)
        self.cleared = False

    async def get_data(self):
        return dict(self._data)

    async def clear(self):
        self.cleared = True


class StoreText(GitHubFileStore):
    def __init__(self, text):
        self._text = text

    async def fetch(self, file_path: str = None):
        return {"sha": "sha0", "text": self._text}

    async def commit(self, *args, file_path=None, **kwargs):
        return {"commit": {"html_url": "https://example.com/commit/d"}}


@pytest.mark.asyncio
async def test_delete_no_and_index_out(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    user = User(id=1, is_bot=False, first_name="U")

    edited = []
    async def edit(self, text, **kwargs):
        edited.append(text)
    async def cq_answer(self, *a, **k):
        return None

    monkeypatch.setattr(Message, "edit_text", edit)
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    # no
    cq_no = CallbackQuery(id="1", from_user=user, chat_instance="ci", data="del:confirm:no", message=m)
    state = FakeState({"delete_idx": 0})
    store = StoreText("DOMAIN,a.com\n")
    await on_del_confirm(cq_no, state, store)
    assert any("Отменено" in t for t in edited) and state.cleared

    # idx out of range
    edited.clear()
    cq_yes = CallbackQuery(id="2", from_user=user, chat_instance="ci", data="del:confirm:yes", message=m)
    state2 = FakeState({"delete_idx": 5})
    await on_del_confirm(cq_yes, state2, store)
    assert any("Не удалось удалить" in t for t in edited) and state2.cleared


@pytest.mark.asyncio
async def test_delete_on_del_page(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    user = User(id=1, is_bot=False, first_name="U")

    edited = []
    async def edit(self, text, **kwargs):
        edited.append(text)
    async def cq_answer(self, *a, **k):
        return None

    monkeypatch.setattr(Message, "edit_text", edit)
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    cq_page = CallbackQuery(id="3", from_user=user, chat_instance="ci", data="del:page:1", message=m)
    # generate enough rules for multiple pages
    text = "\n".join([f"DOMAIN,x{i}.com" for i in range(30)]) + "\n"
    store = StoreText(text)
    # state with previous filter (simulate query)
    class S:
        async def get_data(self):
            return {"delete_filter": "x"}
    await on_del_page(cq_page, S(), store)
    assert edited  # something was edited
