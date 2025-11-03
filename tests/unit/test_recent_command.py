import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.view_config import recent_command


@pytest.mark.asyncio
async def test_recent_command_success():
    store = AsyncMock()
    store.get_recent_commits.return_value = [
        {
            "commit": {
                "message": "Add rule: DOMAIN,example.com",
                "author": {"name": "testuser", "date": "2024-01-15T10:30:00Z"}
            },
            "html_url": "https://github.com/test/repo/commit/abc123"
        }
    ]
    m = MagicMock()
    m.answer = AsyncMock()
    
    await recent_command(m, store)
    
    m.answer.assert_called_once()
    call_text = m.answer.call_args[0][0]
    assert "Последние изменения" in call_text
    assert "Add rule: DOMAIN,example.com" in call_text
    assert "testuser" in call_text
    assert "2024-01-15" in call_text


@pytest.mark.asyncio
async def test_recent_command_no_commits():
    store = AsyncMock()
    store.get_recent_commits.return_value = []
    m = MagicMock()
    m.answer = AsyncMock()
    
    await recent_command(m, store)
    
    m.answer.assert_called_once()
    assert "Нет последних изменений" in m.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_recent_command_error():
    store = AsyncMock()
    store.get_recent_commits.side_effect = Exception("API error")
    m = MagicMock()
    m.answer = AsyncMock()
    
    await recent_command(m, store)
    
    m.answer.assert_called_once()
    assert "Ошибка" in m.answer.call_args[0][0]
