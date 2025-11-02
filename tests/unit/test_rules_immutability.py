"""Test that rules_file operations don't mutate original data."""
from bot.services.rules_file import (
    parse_text,
    clear_policy,
    replace_policy,
    Rule,
    RuleType,
    Policy,
)


def test_clear_policy_no_mutation():
    """Verify clear_policy doesn't mutate original lines."""
    text = "DOMAIN,example.com,PROXY\n"
    lines = parse_text(text)
    original_rule = lines[0].rule
    assert original_rule.policy == Policy.PROXY

    # Clear policy
    new_lines = clear_policy(lines, 0)

    # Original should be unchanged
    assert lines[0].rule.policy == Policy.PROXY
    assert lines[0].rule is original_rule

    # New should have no policy
    assert new_lines[0].rule.policy is None
    assert new_lines[0].rule is not original_rule


def test_replace_policy_no_mutation():
    """Verify replace_policy doesn't mutate original lines."""
    text = "DOMAIN,example.com,PROXY\n"
    lines = parse_text(text)
    original_rule = lines[0].rule
    assert original_rule.policy == Policy.PROXY

    # Replace policy
    new_lines = replace_policy(lines, 0, Policy.DIRECT)

    # Original should be unchanged
    assert lines[0].rule.policy == Policy.PROXY
    assert lines[0].rule is original_rule

    # New should have new policy
    assert new_lines[0].rule.policy == Policy.DIRECT
    assert new_lines[0].rule is not original_rule
