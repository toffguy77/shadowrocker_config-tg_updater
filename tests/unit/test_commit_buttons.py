import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.add_rule import on_confirm
from bot.handlers.delete_rule import on_del_confirm


@pytest.mark.asyncio
async def test_add_rule_commit_button():
    store = AsyncMock()
    store.fetch.return_value = {"text": "", "sha": "abc123"}
    store.commit.return_value = {
        "commit": {"html_url": "https://github.com/test/repo/commit/abc123"}
    }
    
    c = MagicMock()
    c.data = "add:confirm:add"
    c.from_user = MagicMock()
    c.from_user.username = "testuser"
    c.message = MagicMock()
    c.message.edit_text = AsyncMock()
    c.answer = AsyncMock()
    
    state = AsyncMock()
    state.get_data.return_value = {"rule_type": "DOMAIN", "value": "google.com", "policy": "PROXY"}
    state.clear = AsyncMock()
    
    await on_confirm(c, state, store)
    
    c.message.edit_text.assert_called_once()
    call_kwargs = c.message.edit_text.call_args[1]
    assert "reply_markup" in call_kwargs
    markup = call_kwargs["reply_markup"]
    if markup:
        buttons_text = [btn.text for row in markup.inline_keyboard for btn in row]
        assert any("🔗" in btn or "Посмотреть" in btn for btn in buttons_text)


@pytest.mark.asyncio
async def test_delete_rule_commit_button():
    store = AsyncMock()
    store.fetch.return_value = {"text": "DOMAIN,google.com", "sha": "abc123"}
    store.commit.return_value = {
        "commit": {"html_url": "https://github.com/test/repo/commit/abc123"}
    }
    
    c = MagicMock()
    c.data = "del:confirm:yes"
    c.from_user = MagicMock()
    c.from_user.username = "testuser"
    c.message = MagicMock()
    c.message.edit_text = AsyncMock()
    c.answer = AsyncMock()
    
    state = AsyncMock()
    state.get_data.return_value = {"delete_idx": 0, "preview": "DOMAIN,google.com"}
    state.clear = AsyncMock()
    
    await on_del_confirm(c, state, store)
    
    c.message.edit_text.assert_called_once()
    call_kwargs = c.message.edit_text.call_args[1]
    assert "reply_markup" in call_kwargs
    markup = call_kwargs["reply_markup"]
    if markup:
        buttons_text = [btn.text for row in markup.inline_keyboard for btn in row]
        assert any("🔗" in btn or "Посмотреть" in btn for btn in buttons_text)
