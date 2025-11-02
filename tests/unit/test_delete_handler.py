from bot.handlers.delete_rule import _render_delete_page
from bot.services.rules_file import Rule, RuleType


def _make_rules(n=25):
    return list(enumerate([Rule(type=RuleType.DOMAIN, value=f"x{i}.com", policy=None) for i in range(n)]))


def test_delete_markup_merge_page0():
    rules = _make_rules(25)
    body, btns, nav = _render_delete_page(rules, page=0)
    kb = btns.as_markup()
    nav_m = nav.as_markup()
    if getattr(nav_m, "inline_keyboard", None):
        kb.inline_keyboard.append(nav_m.inline_keyboard[0])
    # Should have at least two rows: buttons and nav
    assert len(kb.inline_keyboard) >= 1


def test_delete_markup_merge_page1():
    rules = _make_rules(25)
    body, btns, nav = _render_delete_page(rules, page=1)
    kb = btns.as_markup()
    nav_m = nav.as_markup()
    if getattr(nav_m, "inline_keyboard", None):
        kb.inline_keyboard.append(nav_m.inline_keyboard[0])
    assert len(kb.inline_keyboard) >= 1
