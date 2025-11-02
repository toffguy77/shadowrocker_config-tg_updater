import pytest

from bot.validators.domain import normalize_domain_exact, normalize_domain_suffix
from bot.validators.keyword import normalize_keyword
from bot.validators.ip import normalize_ip


def test_normalize_domain_exact_valid_url():
    ok, val = normalize_domain_exact("https://Sub.Example.com/path?q=1")
    assert ok and val == "sub.example.com"


def test_normalize_domain_exact_invalid():
    ok, err = normalize_domain_exact("not_a_domain")
    assert not ok and "Не удалось распознать домен" in err


def test_normalize_domain_suffix_registrable():
    ok, val = normalize_domain_suffix("news.bbc.co.uk")
    assert ok and val in ("bbc.co.uk", "news.bbc.co.uk")  # allow both depending on PSL availability


def test_normalize_keyword():
    ok, val = normalize_keyword("  Foo-Bar  ")
    assert ok and val == "foo-bar"


def test_normalize_keyword_invalid():
    ok, err = normalize_keyword("bad word")
    assert not ok and "Ключевое слово" in err


def test_normalize_ip_defaults_to_32():
    ok, val = normalize_ip("192.168.0.1")
    assert ok and val.endswith("/32")


def test_normalize_ip_invalid():
    ok, err = normalize_ip("300.1.1.1/33")
    assert not ok and "Некорректный IP-адрес" in err
