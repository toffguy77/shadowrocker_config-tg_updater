import os
import pytest

from bot.config import Settings, get_settings


def test_allowed_users_parsing(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("ALLOWED_USERS", "1, 2, abc,3")
    s = Settings()
    assert s.allowed_users == [1, 2, 3]


def test_allowed_users_empty(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("ALLOWED_USERS", "")
    s = Settings()
    assert s.allowed_users == []


def test_get_settings_cached(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    a = get_settings()
    b = get_settings()
    assert a is b
