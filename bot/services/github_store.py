from __future__ import annotations

import base64
import datetime as dt
import os
import time
from typing import Any, Dict

import aiohttp

from bot.config import Settings
from bot import metrics

GITHUB_API = "https://api.github.com"


class GitHubFileStore:
    def __init__(self, settings: Settings) -> None:
        self.owner = settings.github_owner
        self.repo = settings.github_repo
        self.path = settings.github_path
        self.branch = settings.github_branch
        self.token = settings.github_token

    async def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "tg-shadowrocket-bot/1.0",
        }

    async def fetch(self) -> Dict[str, Any]:
        url = f"{GITHUB_API}/repos/{self.owner}/{self.repo}/contents/{self.path}"
        params = {"ref": self.branch}
        start = time.perf_counter()
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, headers=await self._headers(), params=params) as r:
                    r.raise_for_status()
                    data = await r.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return {"sha": data["sha"], "text": content}
        finally:
            metrics.GITHUB_FETCH_SECONDS.observe(time.perf_counter() - start)

    async def commit(self, new_text: str, message: str, author_name: str | None, author_email: str | None, base_sha: str, retry: int = 1) -> Dict[str, Any]:
        url = f"{GITHUB_API}/repos/{self.owner}/{self.repo}/contents/{self.path}"
        payload = {
            "message": message,
            "content": base64.b64encode(new_text.encode("utf-8")).decode("ascii"),
            "branch": self.branch,
            "sha": base_sha,
        }
        if author_name and author_email:
            payload["committer"] = {"name": "TG Shadowrocket Bot", "email": "bot@users.noreply.github.com"}
            payload["author"] = {"name": author_name, "email": author_email}
        start = time.perf_counter()
        try:
            async with aiohttp.ClientSession() as s:
                async with s.put(url, headers=await self._headers(), json=payload) as r:
                    if r.status == 409 and retry > 0:
                        latest = await self.fetch()
                        return await self.commit(new_text, message, author_name, author_email, latest["sha"], retry=0)
                    r.raise_for_status()
                    return await r.json()
        except Exception:
            metrics.GITHUB_ERRORS.inc()
            raise
        finally:
            metrics.GITHUB_COMMIT_SECONDS.observe(time.perf_counter() - start)

    @staticmethod
    def commit_message_add(rule_line: str, username: str | None) -> str:
        u = f" by @{username}" if username else ""
        return f"Add rule: {rule_line}{u}"

    @staticmethod
    def commit_message_delete(rule_line: str, username: str | None) -> str:
        u = f" by @{username}" if username else ""
        return f"Delete rule: {rule_line}{u}"

    @staticmethod
    def added_comment(username: str | None, now: dt.datetime | None = None) -> str:
        if now is None:
            now = dt.datetime.utcnow()
        uname = f"@{username}" if username else "unknown"
        ts = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"# Added: {ts} | User: {uname}"

    @staticmethod
    def removed_comment(username: str | None, now: dt.datetime | None = None) -> str:
        if now is None:
            now = dt.datetime.utcnow()
        uname = f"@{username}" if username else "unknown"
        ts = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"# Removed: {ts} | User: {uname}"
