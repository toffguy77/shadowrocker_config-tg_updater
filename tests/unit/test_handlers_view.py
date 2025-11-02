import datetime as dt
import pytest
from aiogram.types import Message, Chat, CallbackQuery, User

from bot.handlers.view_config import on_view_pager
from bot.services.github_store import GitHubFileStore


class StoreFail(GitHubFileStore):
    def __init__(self):
        pass
    async def fetch(self):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_view_pager_error_alert(monkeypatch):
    m = Message(message_id=1, date=dt.datetime.now(dt.timezone.utc), chat=Chat(id=1, type="private"))
    user = User(id=1, is_bot=False, first_name="U")
    cq = CallbackQuery(id="1", from_user=user, chat_instance="ci", data="view:ALL:page:1", message=m)

    # patch answer to ensure no exception and capture call
    called = {"alert": False}
    async def cq_answer(self, text=None, show_alert=False, **kwargs):
        called["alert"] = show_alert
    monkeypatch.setattr(CallbackQuery, "answer", cq_answer)

    await on_view_pager(cq, StoreFail())
    assert called["alert"] is True
