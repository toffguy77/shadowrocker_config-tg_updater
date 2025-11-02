import pytest
from bot.metrics import INPUT_VALID, INPUT_INVALID, GITHUB_ERRORS


def test_input_valid_has_type_label():
    # Verify metric accepts type label
    INPUT_VALID.labels(type="DOMAIN").inc()
    INPUT_VALID.labels(type="IP-CIDR").inc()
    # Should not raise


def test_input_invalid_has_type_label():
    INPUT_INVALID.labels(type="DOMAIN-SUFFIX").inc()
    # Should not raise


def test_github_errors_has_operation_label():
    GITHUB_ERRORS.labels(operation="fetch").inc()
    GITHUB_ERRORS.labels(operation="commit").inc()
    # Should not raise
