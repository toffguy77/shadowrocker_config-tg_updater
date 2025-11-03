from bot.handlers.view_config import _render_page
from bot.services.rules_file import Rule, RuleType


def test_render_page_sorted_and_paged():
    # Build unsorted rules: values z..a
    vals = ["z.com", "a.com", "m.com", "b.com"] + [f"x{i}.com" for i in range(30)]
    rules = list(enumerate([Rule(type=RuleType.DOMAIN, value=v, policy=None) for v in vals]))

    body, kb = _render_page(rules, page=0, rule_type="ALL", all_rules=rules)
    assert "📋 Показано:" in body
    # First page should include 20 items; ensure 'a.com' appears before 'b.com' and 'z.com'
    a_idx = body.find("a.com")
    b_idx = body.find("b.com")
    z_idx = body.find("z.com")
    assert -1 < a_idx < b_idx
    assert z_idx == -1  # z.com should be on the next page due to sorting

    # Next page should be available
    markup = kb.as_markup()
    flat = [btn.callback_data for row in getattr(markup, "inline_keyboard", []) for btn in row]
    assert any(cd and cd.endswith(":page:1") for cd in flat)

    # Page 1
    body2, kb2 = _render_page(rules, page=1, rule_type="ALL", all_rules=rules)
    assert "📋 Показано:" in body2
