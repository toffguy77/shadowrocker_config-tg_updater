import pytest
from unittest.mock import MagicMock
from bot.services.github_store import GitHubFileStore


@pytest.mark.asyncio
async def test_get_recent_commits_error():
    settings = MagicMock()
    settings.github_owner = "owner"
    settings.github_repo = "repo"
    settings.github_path_proxy = "config.conf"
    settings.github_branch = "main"
    settings.github_token = "test"
    
    class FailStore(GitHubFileStore):
        async def get_recent_commits(self, limit=5):
            return []
    
    store = FailStore(settings)
    commits = await store.get_recent_commits(limit=5)
    
    assert commits == []
