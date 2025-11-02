import base64
import pytest
from aioresponses import aioresponses, CallbackResult

from bot.services.github_store import GitHubFileStore
from bot.config import Settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_store_fetch_success(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    content = base64.b64encode(b"hello world\n").decode("ascii")
    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path}"

    with aioresponses() as m:
        m.get(f"{url}?ref=main", payload={"content": content, "sha": "abc"}, status=200)
        result = await store.fetch()

    assert result["sha"] == "abc"
    assert result["text"].startswith("hello world")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_store_commit_success(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)
    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path}"

    payload_captured = {}

    with aioresponses() as m:
        def _cb(url, **kwargs):
            payload_captured.update(kwargs.get("json", {}))
            return CallbackResult(status=200, payload={"commit": {"html_url": "https://github.com/o/r/commit/1"}})
        m.put(url, callback=_cb)
        resp = await store.commit("text", "msg", "name", "email", base_sha="abc")

    assert resp.get("commit", {}).get("html_url")
    assert payload_captured["sha"] == "abc"
