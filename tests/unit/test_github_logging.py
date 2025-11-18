"""Test GitHub store logging improvements."""
import pytest
import logging
from aioresponses import aioresponses

from bot.services.github_store import GitHubFileStore
from bot.config import Settings


@pytest.mark.asyncio
async def test_commit_logs_context(monkeypatch, caplog):
    """Test that commit logs include context (message, author, sha)."""
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH_PROXY", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path_proxy}"

    with caplog.at_level(logging.INFO):
        with aioresponses() as m:
            m.put(url, payload={"commit": {"html_url": "https://example.com/commit/1"}}, status=200)
            await store.commit("text", "Add rule: example.com", "testuser", None, base_sha="abc123def")

    # Check that log contains context
    log_messages = [record.message for record in caplog.records]
    assert any("Committing to GitHub" in msg for msg in log_messages)
    assert any("testuser" in msg for msg in log_messages)
    assert any("abc123d" in msg for msg in log_messages)  # short sha


@pytest.mark.asyncio
async def test_commit_success_logs(monkeypatch, caplog):
    """Test that successful commit is logged."""
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH_PROXY", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path_proxy}"

    with caplog.at_level(logging.INFO):
        with aioresponses() as m:
            m.put(url, payload={"commit": {"html_url": "https://example.com/commit/1"}}, status=200)
            await store.commit("text", "Test commit", None, None, base_sha="sha")

    log_messages = [record.message for record in caplog.records]
    assert any("GitHub commit success" in msg for msg in log_messages)


@pytest.mark.asyncio
async def test_conflict_retry_logs(monkeypatch, caplog):
    """Test that 409 conflict retry is logged."""
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OWNER", "o")
    monkeypatch.setenv("GITHUB_REPO", "r")
    monkeypatch.setenv("GITHUB_PATH_PROXY", "p.txt")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    settings = Settings()
    store = GitHubFileStore(settings)

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{settings.github_path_proxy}"
    get_url = f"{url}?ref=main"

    with caplog.at_level(logging.WARNING):
        with aioresponses() as m:
            m.put(url, status=409)
            m.get(get_url, payload={"content": "aGVsbG8=", "sha": "new_sha"}, status=200)
            m.put(url, payload={"commit": {"html_url": "https://example.com/commit/1"}}, status=200)
            await store.commit("text", "msg", None, None, base_sha="old_sha")

    log_messages = [record.message for record in caplog.records]
    assert any("conflict" in msg.lower() and "409" in msg for msg in log_messages)
