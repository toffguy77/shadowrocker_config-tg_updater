import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.url_check import url_check_command


@pytest.mark.asyncio
async def test_url_check_success():
    store = AsyncMock()
    store.fetch.return_value = {
        "text": "OK: rules/private.dedup.list — формат в порядке, warnings: 0",
        "sha": "abc123"
    }
    m = MagicMock()
    m.answer = AsyncMock()
    
    await url_check_command(m, store)
    
    m.answer.assert_called_once()
    assert "Все URL доступны" in m.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_url_check_with_errors():
    store = AsyncMock()
    store.fetch.return_value = {
        "text": "ERROR: 2 RULE-SET URL(s) unreachable\n1234: HTTP 404 -- https://example.com/rules.list",
        "sha": "abc123"
    }
    m = MagicMock()
    m.answer = AsyncMock()
    
    await url_check_command(m, store)
    
    m.answer.assert_called_once()
    call_text = m.answer.call_args[0][0]
    assert "Недоступные URL" in call_text
    assert "unreachable" in call_text or "404" in call_text


@pytest.mark.asyncio
async def test_url_check_empty_log():
    store = AsyncMock()
    store.fetch.return_value = {"text": "", "sha": "abc123"}
    m = MagicMock()
    m.answer = AsyncMock()
    
    await url_check_command(m, store)
    
    m.answer.assert_called_once()
    assert "пуст" in m.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_url_check_not_found():
    store = AsyncMock()
    store.fetch.side_effect = Exception("File not found")
    m = MagicMock()
    m.answer = AsyncMock()
    
    await url_check_command(m, store)
    
    m.answer.assert_called_once()
    assert "не найден" in m.answer.call_args[0][0]
