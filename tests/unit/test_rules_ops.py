from bot.services.rules_file import parse_text, list_rules, find_rule_index, add_rule as rf_add_rule, clear_policy as rf_clear_policy, delete_rule as rf_delete_rule, render_lines, Rule, RuleType, Policy

SAMPLE = """
# header
DOMAIN,foo.com,PROXY
DOMAIN,bar.com,DIRECT
""".strip()

def test_find_and_add_and_delete():
    lines = parse_text(SAMPLE)
    rules = list_rules(lines)
    # find foo.com
    idx = find_rule_index(lines, RuleType.DOMAIN, "foo.com")
    assert idx is not None

    # add new rule
    new_rule = Rule(type=RuleType.DOMAIN, value="baz.com", policy=None)
    new_lines = rf_add_rule(lines, new_rule, "# Added")
    text = render_lines(new_lines)
    assert "DOMAIN,baz.com" in text

    # delete the newly added rule (last line)
    lines2 = parse_text(text)
    rules2 = list_rules(lines2)
    idx2 = find_rule_index(lines2, RuleType.DOMAIN, "baz.com")
    assert idx2 is not None
    after = rf_delete_rule(lines2, idx2, removed_comment="# Removed")
    text2 = render_lines(after)
    # soft-deleted: the rule is commented out and not active
    assert "# DOMAIN,baz.com" in text2
    assert find_rule_index(parse_text(text2), RuleType.DOMAIN, "baz.com") is None


def test_clear_policy_renders_two_columns():
    # take first rule with policy from SAMPLE
    lines = parse_text(SAMPLE)
    idx = find_rule_index(lines, RuleType.DOMAIN, "foo.com")
    assert idx is not None
    updated = rf_clear_policy(lines, idx)
    text = render_lines(updated)
    # policy must be dropped
    assert "DOMAIN,foo.com\n" in text
    assert ",PROXY" not in text
