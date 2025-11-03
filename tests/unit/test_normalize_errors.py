import datetime as dt
import pytest
from unittest.mock import MagicMock, AsyncMock
from aiogram.types import Message, Chat, User

from bot.handlers.normalize import normalize_config
from bot.services.github_store import GitHubFileStore


class FailingStore(GitHubFileStore):
    def __init__(self):
        pass

    async def fetch(self):
        raise Exception("Network error")


@pytest.mark.asyncio
async def test_normalize_handles_fetch_error(monkeypatch):
    """Test that normalize handles GitHub fetch errors gracefully."""
    store = FailingStore()
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=123, is_bot=False, first_name="Test")
    )
    
    sent = []
    
    async def m_answer(self, text, **kwargs):
        sent.append(text)
        mock_msg = MagicMock()
        mock_msg.edit_text = AsyncMock(side_effect=lambda t, **kw: sent.append(t))
        return mock_msg
    
    monkeypatch.setattr(Message, "answer", m_answer)
    
    await normalize_config(m, store)
    
    assert any("❌ Ошибка нормализации" in t for t in sent)


class CommitFailStore(GitHubFileStore):
    def __init__(self):
        pass

    async def fetch(self):
        return {"sha": "abc", "text": "DOMAIN,test.com,PROXY\n"}

    async def commit(self, *args, **kwargs):
        raise Exception("Commit failed")


@pytest.mark.asyncio
async def test_normalize_handles_commit_error(monkeypatch):
    """Test that normalize handles GitHub commit errors gracefully."""
    store = CommitFailStore()
    m = Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=123, is_bot=False, first_name="Test")
    )
    
    sent = []
    
    async def m_answer(self, text, **kwargs):
        sent.append(text)
        mock_msg = MagicMock()
        mock_msg.edit_text = AsyncMock(side_effect=lambda t, **kw: sent.append(t))
        return mock_msg
    
    monkeypatch.setattr(Message, "answer", m_answer)
    
    await normalize_config(m, store)
    
    assert any("❌ Ошибка нормализации" in t for t in sent)
