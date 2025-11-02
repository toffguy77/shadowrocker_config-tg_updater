import base64
import datetime as dt
import pytest

from bot.services.rules_file import parse_text, list_rules, render_lines, Rule, RuleType, Policy, describe_rule

SAMPLE = """
# Comment
DOMAIN-SUFFIX,example.com,PROXY
DOMAIN,exact.com,DIRECT
DOMAIN-KEYWORD,shop,REJECT
IP-CIDR,10.0.0.0/8,DIRECT
""".strip()


def test_parse_and_list_rules():
    lines = parse_text(SAMPLE)
    rules = list_rules(lines)
    assert len(rules) == 4
    # First rule
    _, r1 = rules[0]
    assert r1.type == RuleType.DOMAIN_SUFFIX
    assert r1.value == "example.com"
    assert r1.policy == Policy.PROXY


def test_render_roundtrip():
    lines = parse_text(SAMPLE)
    text = render_lines(lines)
    assert "DOMAIN-SUFFIX,example.com" in text
    assert ",PROXY" not in text
    assert text.endswith("\n")


def test_describe_rule():
    r = Rule(type=RuleType.DOMAIN, value="site.com", policy=Policy.DIRECT)
    s = describe_rule(r)
    assert "site.com" in s and "DIRECT" not in s
