import base64
import asyncio
import pytest

from bot.handlers.view_config import build_view_response

SAMPLE_TEXT = """
# c
DOMAIN,example.com,PROXY
DOMAIN,another.com,DIRECT
""".strip()


class FakeStore:
    def __init__(self, text=SAMPLE_TEXT):
        self._text = text

    async def fetch(self):
        return {"sha": "sha", "text": self._text}


@pytest.mark.asyncio
async def test_build_view_response_all():
    store = FakeStore()
    body, markup = await build_view_response(store, policy="ALL", page=0)
    assert "Показано: 2" in body
    assert hasattr(markup, "inline_keyboard")


@pytest.mark.asyncio
async def test_build_view_response_empty():
    store = FakeStore(text="# empty")
    body, _ = await build_view_response(store, policy="ALL", page=0)
    assert "Конфиг пуст" in body
