"""Test GitHub store error handling and retries."""
import pytest
from aioresponses import aioresponses
import aiohttp

from bot.services.github_store import GitHubFileStore
from bot.config import Settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_fetch_timeout(monkeypatch):
    """Test that fetch handles timeouts properly."""
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path}"

    with aioresponses() as m:
        m.get(f"{url}?ref=main", exception=aiohttp.ClientError("timeout"))
        with pytest.raises(aiohttp.ClientError):
            await store.fetch()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_commit_409_retry(monkeypatch):
    """Test that commit retries on 409 conflict."""
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path}"
    get_url = f"{url}?ref=main"

    with aioresponses() as m:
        # First commit attempt returns 409
        m.put(url, status=409)
        # Fetch for retry
        m.get(get_url, payload={"content": "aGVsbG8=", "sha": "new_sha"}, status=200)
        # Second commit succeeds
        m.put(url, payload={"commit": {"html_url": "https://example.com/commit/1"}}, status=200)

        result = await store.commit("text", "msg", None, None, base_sha="old_sha")
        assert result["commit"]["html_url"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_commit_500_retry(monkeypatch):
    """Test that commit retries on 500 server error."""
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path}"
    get_url = f"{url}?ref=main"

    with aioresponses() as m:
        # First commit attempt returns 500
        m.put(url, status=500, body="Internal Server Error")
        # Fetch for retry
        m.get(get_url, payload={"content": "aGVsbG8=", "sha": "new_sha"}, status=200)
        # Second commit succeeds
        m.put(url, payload={"commit": {"html_url": "https://example.com/commit/1"}}, status=200)

        result = await store.commit("text", "msg", None, None, base_sha="old_sha")
        assert result["commit"]["html_url"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_commit_400_no_retry(monkeypatch):
    """Test that commit doesn't retry on 400 client error."""
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path}"

    with aioresponses() as m:
        m.put(url, status=400, body="Bad Request")
        with pytest.raises(aiohttp.ClientResponseError):
            await store.commit("text", "msg", None, None, base_sha="sha")
