import pytest
from bot.validators.domain import normalize_domain_exact, normalize_domain_suffix


def test_domain_label_too_long():
    # Label with 64 characters (max is 63)
    long_label = "a" * 64
    domain = f"{long_label}.com"
    ok, msg = normalize_domain_exact(domain)
    assert not ok
    assert "63" in msg


def test_domain_label_max_valid():
    # Label with exactly 63 characters (should pass)
    max_label = "a" * 63
    domain = f"{max_label}.com"
    ok, result = normalize_domain_exact(domain)
    assert ok
    assert result == domain


def test_domain_suffix_label_too_long():
    long_label = "a" * 64
    domain = f"sub.{long_label}.com"
    ok, msg = normalize_domain_suffix(domain)
    assert not ok
    assert "63" in msg


def test_multiple_labels_one_too_long():
    domain = f"short.{'b' * 64}.example.com"
    ok, msg = normalize_domain_exact(domain)
    assert not ok
    assert "63" in msg
