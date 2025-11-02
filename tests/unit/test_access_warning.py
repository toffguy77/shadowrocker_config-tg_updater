import logging
import pytest
from bot.middlewares.access import AccessMiddleware


def test_access_middleware_warns_on_empty_users(caplog):
    with caplog.at_level(logging.WARNING):
        middleware = AccessMiddleware(allowed_users=[])
    
    assert any("ALLOWED_USERS is empty" in record.message for record in caplog.records)
    assert any("accessible to everyone" in record.message for record in caplog.records)


def test_access_middleware_no_warning_with_users(caplog):
    with caplog.at_level(logging.WARNING):
        middleware = AccessMiddleware(allowed_users=[123, 456])
    
    assert not any("ALLOWED_USERS" in record.message for record in caplog.records)
