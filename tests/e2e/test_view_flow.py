import datetime as dt
import pytest
from aiogram.types import Message, Chat

from bot.handlers.view_config import view_config


class FakeStore:
    def __init__(self, text):
        self._text = text

    async def fetch(self):
        return {"sha": "1", "text": self._text}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_view_config_message_flow(monkeypatch):
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
    )

    sent = {"text": None}

    async def fake_answer(self, text, **kwargs):
        sent["text"] = text

    monkeypatch.setattr(Message, "answer", fake_answer)

    store = FakeStore("DOMAIN,example.com,PROXY\n")
    await view_config(m, store)

    assert sent["text"] and "Показано:" in sent["text"]
