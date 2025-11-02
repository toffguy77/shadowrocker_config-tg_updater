import pytest

from bot.metrics import start_metrics_server


class Ctx:
    called = []


def _fake_start_http_server(port, addr="127.0.0.1"):
    Ctx.called.append((port, addr))


@pytest.mark.asyncio
async def test_start_metrics_server(monkeypatch):
    monkeypatch.setattr("bot.metrics.start_http_server", _fake_start_http_server)
    Ctx.called.clear()

    start_metrics_server("127.0.0.1:9999")
    assert Ctx.called[-1] == (9999, "127.0.0.1")

    start_metrics_server(":")
    assert Ctx.called[-1] == (9123, "0.0.0.0")
