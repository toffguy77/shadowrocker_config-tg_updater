"""Tests for policy-based file selection functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.config import Settings
from bot.services.github_store import GitHubFileStore
from bot.models.enums import Policy


def test_config_new_fields():
    """Test that configuration includes both proxy and direct file paths."""
    settings = Settings(
        BOT_TOKEN="test",
        GITHUB_TOKEN="test",
        GITHUB_PATH_PROXY="rules/private.list",
        GITHUB_PATH_DIRECT="rules/private.direct.list"
    )
    
    assert settings.github_path_proxy == "rules/private.list"
    assert settings.github_path_direct == "rules/private.direct.list"


def test_github_store_policy_mapping():
    """Test that GitHubFileStore correctly maps policies to file paths."""
    settings = Settings(
        BOT_TOKEN="test",
        GITHUB_TOKEN="test",
        GITHUB_PATH_PROXY="rules/private.list",
        GITHUB_PATH_DIRECT="rules/private.direct.list"
    )
    
    store = GitHubFileStore(settings)
    
    # Test PROXY policy maps to proxy path
    proxy_path = store.get_path_for_policy(Policy.PROXY.value)
    assert proxy_path == "rules/private.list"
    
    # Test DIRECT policy maps to direct path
    direct_path = store.get_path_for_policy(Policy.DIRECT.value)
    assert direct_path == "rules/private.direct.list"
    
    # Test REJECT policy maps to proxy path (fallback)
    reject_path = store.get_path_for_policy(Policy.REJECT.value)
    assert reject_path == "rules/private.list"


class MockStoreWithPolicy:
    """Mock store that supports policy-based file selection."""
    
    def __init__(self, proxy_text="", direct_text=""):
        self.proxy_text = proxy_text
        self.direct_text = direct_text
        self.path_proxy = "rules/private.list"
        self.path_direct = "rules/private.direct.list"
    
    def get_path_for_policy(self, policy: str) -> str:
        if policy == Policy.DIRECT.value:
            return self.path_direct
        return self.path_proxy
    
    async def fetch(self, file_path: str = None):
        if file_path == self.path_direct:
            return {"text": self.direct_text, "sha": "direct123"}
        return {"text": self.proxy_text, "sha": "proxy123"}
    
    async def commit(self, new_text: str, message: str, author_name: str | None, 
                    author_email: str | None, base_sha: str, file_path: str = None):
        return {"commit": {"html_url": "https://github.com/test/commit/123"}}


@pytest.mark.asyncio
async def test_mock_store_policy_selection():
    """Test that mock store correctly returns different content based on policy."""
    store = MockStoreWithPolicy(
        proxy_text="DOMAIN,proxy.com\n",
        direct_text="DOMAIN,direct.com\n"
    )
    
    # Test proxy file
    proxy_result = await store.fetch(file_path=store.get_path_for_policy(Policy.PROXY.value))
    assert "proxy.com" in proxy_result["text"]
    
    # Test direct file
    direct_result = await store.fetch(file_path=store.get_path_for_policy(Policy.DIRECT.value))
    assert "direct.com" in direct_result["text"]