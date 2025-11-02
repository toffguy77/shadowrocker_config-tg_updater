from bot.keyboards.confirm import confirm_add_kb, confirm_replace_kb
from bot.keyboards.rule_type import rule_type_kb


def _flat_callbacks(markup):
    return [btn.callback_data for row in markup.inline_keyboard for btn in row]


def test_confirm_add_kb_callbacks():
    kb = confirm_add_kb().as_markup()
    calls = _flat_callbacks(kb)
    assert "add:confirm:add" in calls
    assert "add:confirm:cancel" in calls


def test_confirm_replace_kb_callbacks():
    kb = confirm_replace_kb().as_markup()
    calls = _flat_callbacks(kb)
    assert {"add:confirm:replace", "add:confirm:keep", "add:confirm:cancel"}.issubset(calls)


def test_rule_type_kb_contains_all():
    kb = rule_type_kb().as_markup()
    calls = set(_flat_callbacks(kb))
    expected = {
        "add:type:DOMAIN-SUFFIX",
        "add:type:DOMAIN",
        "add:type:DOMAIN-KEYWORD",
        "add:type:IP-CIDR",
        "add:back:menu",
    }
    assert expected.issubset(calls)
