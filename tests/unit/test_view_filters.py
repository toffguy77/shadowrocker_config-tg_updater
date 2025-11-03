import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.view_config import build_view_response


@pytest.mark.asyncio
async def test_view_filter_by_type():
    store = AsyncMock()
    store.fetch.return_value = {
        "text": "DOMAIN,google.com\nDOMAIN-SUFFIX,facebook.com\nIP-CIDR,1.1.1.1/32",
        "sha": "abc123"
    }
    
    body, markup = await build_view_response(store, rule_type="DOMAIN")
    
    assert "google.com" in body
    assert "facebook.com" not in body
    assert "1.1.1.1" not in body


@pytest.mark.asyncio
async def test_view_filter_all():
    store = AsyncMock()
    store.fetch.return_value = {
        "text": "DOMAIN,google.com\nDOMAIN-SUFFIX,facebook.com",
        "sha": "abc123"
    }
    
    body, markup = await build_view_response(store, rule_type="ALL")
    
    assert "google.com" in body
    assert "facebook.com" in body


@pytest.mark.asyncio
async def test_view_shows_statistics():
    store = AsyncMock()
    store.fetch.return_value = {
        "text": "DOMAIN,google.com\nDOMAIN,yahoo.com\nIP-CIDR,1.1.1.1/32",
        "sha": "abc123"
    }
    
    body, markup = await build_view_response(store, rule_type="ALL")
    
    assert "DOMAIN: 2" in body
    assert "IP-CIDR: 1" in body


@pytest.mark.asyncio
async def test_view_download_button():
    store = AsyncMock()
    store.fetch.return_value = {
        "text": "DOMAIN,google.com",
        "sha": "abc123"
    }
    
    body, markup = await build_view_response(store, rule_type="ALL")
    
    assert markup.inline_keyboard
    buttons_text = [btn.text for row in markup.inline_keyboard for btn in row]
    assert "💾 Скачать" in buttons_text
