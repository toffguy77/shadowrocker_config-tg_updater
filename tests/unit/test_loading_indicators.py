import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.add_rule import on_enter_value, AddRule
from bot.handlers.delete_rule import on_delete_query, DeleteRule
from bot.handlers.normalize import normalize_config


@pytest.mark.asyncio
async def test_add_rule_shows_loading():
    store = AsyncMock()
    store.fetch.return_value = {"text": "", "sha": "abc123"}
    
    m = MagicMock()
    loading_msg = MagicMock()
    loading_msg.delete = AsyncMock()
    m.answer = AsyncMock(return_value=loading_msg)
    m.text = "google.com"
    
    state = AsyncMock()
    state.get_data.return_value = {"rule_type": "DOMAIN", "policy": "PROXY"}
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    
    await on_enter_value(m, state, store)
    
    assert m.answer.call_count >= 1
    first_call = m.answer.call_args_list[0][0][0]
    assert "⏳" in first_call or "Проверяю" in first_call


@pytest.mark.asyncio
async def test_delete_shows_loading():
    store = AsyncMock()
    store.fetch.return_value = {"text": "DOMAIN,google.com", "sha": "abc123"}
    
    m = MagicMock()
    loading_msg = MagicMock()
    loading_msg.delete = AsyncMock()
    loading_msg.edit_text = AsyncMock()
    m.answer = AsyncMock(return_value=loading_msg)
    m.text = "google"
    
    state = AsyncMock()
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    
    await on_delete_query(m, state, store)
    
    assert m.answer.call_count >= 1
    first_call = m.answer.call_args_list[0][0][0]
    assert "⏳" in first_call or "Ищу" in first_call


@pytest.mark.asyncio
async def test_normalize_shows_loading():
    store = AsyncMock()
    store.fetch.return_value = {"text": "DOMAIN,google.com,DIRECT", "sha": "abc123"}
    store.commit.return_value = {"commit": {"html_url": "https://github.com"}}
    
    m = MagicMock()
    m.from_user = MagicMock()
    m.from_user.username = "testuser"
    loading_msg = MagicMock()
    loading_msg.edit_text = AsyncMock()
    m.answer = AsyncMock(return_value=loading_msg)
    
    await normalize_config(m, store)
    
    m.answer.assert_called_once()
    first_call = m.answer.call_args[0][0]
    assert "⏳" in first_call or "Нормализую" in first_call
