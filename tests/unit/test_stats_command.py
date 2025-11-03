import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.view_config import stats_command


@pytest.mark.asyncio
async def test_stats_command_success():
    store = AsyncMock()
    store.fetch.return_value = {
        "text": "DOMAIN,google.com\nDOMAIN-SUFFIX,facebook.com\nIP-CIDR,1.1.1.1/32\nDOMAIN-KEYWORD,ads",
        "sha": "abc123"
    }
    m = MagicMock()
    m.answer = AsyncMock()
    
    await stats_command(m, store)
    
    m.answer.assert_called_once()
    call_text = m.answer.call_args[0][0]
    assert "Статистика правил" in call_text
    assert "Всего: 4" in call_text
    assert "DOMAIN:" in call_text
    assert "DOMAIN-SUFFIX:" in call_text
    assert "IP-CIDR:" in call_text
    assert "DOMAIN-KEYWORD:" in call_text


@pytest.mark.asyncio
async def test_stats_command_empty_config():
    store = AsyncMock()
    store.fetch.return_value = {"text": "", "sha": "abc123"}
    m = MagicMock()
    m.answer = AsyncMock()
    
    await stats_command(m, store)
    
    m.answer.assert_called_once()
    call_text = m.answer.call_args[0][0]
    assert "Всего: 0" in call_text


@pytest.mark.asyncio
async def test_stats_command_error():
    store = AsyncMock()
    store.fetch.side_effect = Exception("Network error")
    m = MagicMock()
    m.answer = AsyncMock()
    
    await stats_command(m, store)
    
    m.answer.assert_called_once()
    assert "Ошибка" in m.answer.call_args[0][0]
