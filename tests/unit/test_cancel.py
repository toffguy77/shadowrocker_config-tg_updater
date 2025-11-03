import datetime as dt
import pytest
from aiogram.types import Message, Chat

from bot.handlers.add_rule import on_enter_value, AddRule


class FakeState:
    def __init__(self):
        self._data = {"rule_type": "DOMAIN"}
        self.cleared = False

    async def get_data(self):
        return self._data

    async def clear(self):
        self.cleared = True

    async def set_state(self, *_args, **_kwargs):
        pass

    async def update_data(self, **kwargs):
        self._data.update(kwargs)


class FakeStore:
    async def fetch(self):
        return {"sha": "sha", "text": "# empty\n"}


@pytest.mark.asyncio
async def test_cancel_inline_in_entering_value(monkeypatch):
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        text="/cancel",
    )
    sent = {"text": None}

    async def fake_answer(self, text, **kwargs):
        sent["text"] = text

    monkeypatch.setattr(Message, "answer", fake_answer)

    state = FakeState()
    store = FakeStore()

    await on_enter_value(m, state, store)

    assert state.cleared is True
    assert "Отменено" in sent["text"]
