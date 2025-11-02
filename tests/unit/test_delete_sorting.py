import pytest
from bot.handlers.delete_rule import _render_delete_page
from bot.services.rules_file import Rule, RuleType


def test_delete_page_preserves_file_indices():
    """Test that sorting doesn't break file index mapping."""
    rules = [
        (5, Rule(type=RuleType.DOMAIN, value="zzz.com", policy=None)),
        (2, Rule(type=RuleType.DOMAIN, value="aaa.com", policy=None)),
        (8, Rule(type=RuleType.DOMAIN, value="mmm.com", policy=None)),
    ]
    
    body, builder, nav = _render_delete_page(rules, page=0)
    
    # Check that body is sorted alphabetically
    lines = body.split("\n")
    assert "aaa.com" in lines[2]  # First rule after header
    assert "mmm.com" in lines[3]
    assert "zzz.com" in lines[4]
    
    # Check that buttons use correct file indices
    markup = builder.as_markup()
    buttons = [btn for row in markup.inline_keyboard for btn in row]
    assert len(buttons) == 3
    
    # First button should reference file index 2 (aaa.com)
    assert "del:pick:2:" in buttons[0].callback_data
    # Second button should reference file index 8 (mmm.com)
    assert "del:pick:8:" in buttons[1].callback_data
    # Third button should reference file index 5 (zzz.com)
    assert "del:pick:5:" in buttons[2].callback_data


def test_delete_page_button_text_shows_rule():
    """Test that button text shows rule content, not just numbers."""
    rules = [
        (0, Rule(type=RuleType.DOMAIN, value="example.com", policy=None)),
        (1, Rule(type=RuleType.IP_CIDR, value="10.0.0.0/8", policy=None)),
    ]
    
    body, builder, nav = _render_delete_page(rules, page=0)
    
    markup = builder.as_markup()
    buttons = [btn for row in markup.inline_keyboard for btn in row]
    # Buttons should show rule content (truncated to 20 chars)
    # After sorting: 10.0.0.0/8 comes before example.com alphabetically
    assert "10.0.0.0/8" in buttons[0].text
    assert "example.com" in buttons[1].text
    # Verify callback_data uses original file indices
    assert "del:pick:1:" in buttons[0].callback_data  # IP rule was at index 1
    assert "del:pick:0:" in buttons[1].callback_data  # DOMAIN rule was at index 0
