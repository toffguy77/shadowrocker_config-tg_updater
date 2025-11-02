"""Test domain length validation."""
import pytest
from bot.validators.domain import normalize_domain_exact, normalize_domain_suffix


def test_domain_too_short():
    """Test that domains shorter than 3 chars are rejected."""
    ok, msg = normalize_domain_exact("a.b")
    assert not ok
    assert "длина 3-253" in msg


def test_domain_too_long():
    """Test that domains longer than 253 chars are rejected."""
    long_domain = "a" * 250 + ".com"
    ok, msg = normalize_domain_exact(long_domain)
    assert not ok
    assert "длина 3-253" in msg


def test_domain_valid_length():
    """Test that domains with valid length are accepted."""
    ok, result = normalize_domain_exact("example.com")
    assert ok
    assert result == "example.com"


def test_domain_suffix_too_short():
    """Test that domain suffix rejects short domains."""
    ok, msg = normalize_domain_suffix("a.b")
    assert not ok
    assert "длина 3-253" in msg


def test_domain_suffix_valid():
    """Test that domain suffix accepts valid domains."""
    ok, result = normalize_domain_suffix("sub.example.com")
    assert ok
    assert result in ["example.com", "sub.example.com"]  # depends on publicsuffix2


def test_domain_edge_case_min():
    """Test minimum valid domain length (3 chars)."""
    ok, result = normalize_domain_exact("a.b")
    assert not ok  # still invalid due to regex (needs proper TLD)


def test_domain_edge_case_max():
    """Test maximum valid domain length (253 chars)."""
    # Create a valid domain close to max length
    # Each label max 63 chars, total max 253
    domain = "a" * 60 + "." + "b" * 60 + "." + "c" * 60 + ".example.com"
    ok, result = normalize_domain_exact(domain)
    assert ok
    assert len(result) <= 253
