import asyncio
import datetime as dt
import pytest

from aiogram.types import Message, CallbackQuery, Chat, User

from bot.middlewares.access import AccessMiddleware


@pytest.mark.asyncio
async def test_access_middleware_allows_user(monkeypatch):
    mw = AccessMiddleware([123])

    # Minimal Message
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=123, is_bot=False, first_name="U"),
    )

    called = {"v": False}

    async def handler(event, data):
        called["v"] = True
        return "ok"

    res = await mw(handler, m, {})
    assert called["v"] is True
    assert res == "ok"


@pytest.mark.asyncio
async def test_access_middleware_denies_message(monkeypatch):
    mw = AccessMiddleware([999])

    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=123, is_bot=False, first_name="U"),
    )

    # Prevent network call on answer
    async def fake_answer(*args, **kwargs):
        return None

    monkeypatch.setattr(Message, "answer", fake_answer)

    async def handler(event, data):
        assert False, "handler should not be called"

    res = await mw(handler, m, {})
    assert res is None


@pytest.mark.asyncio
async def test_access_middleware_denies_callback(monkeypatch):
    mw = AccessMiddleware([999])

    msg = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=123, is_bot=False, first_name="U"),
    )
    cq = CallbackQuery(id="1", from_user=msg.from_user, chat_instance="ci", data="x", message=msg)

    async def fake_cq_answer(*args, **kwargs):
        return None

    monkeypatch.setattr(CallbackQuery, "answer", fake_cq_answer)

    async def handler(event, data):
        assert False, "handler should not be called"

    res = await mw(handler, cq, {})
    assert res is None
