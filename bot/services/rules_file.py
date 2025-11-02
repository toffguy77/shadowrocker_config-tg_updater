from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from bot.models.enums import Policy, RuleType


@dataclass
class Rule:
    type: RuleType
    value: str
    policy: Optional[Policy]  # some repos may omit policy (2 columns)


@dataclass
class Line:
    kind: str  # "comment" | "rule" | "other"
    text: str
    rule: Optional[Rule] = None


RULE_RE = re.compile(r"^\s*([A-Z\-]+)\s*,\s*([^,#]+?)\s*(?:,\s*([A-Z]+)\s*)?$")


def parse_text(text: str) -> List[Line]:
    lines: List[Line] = []
    for raw in text.splitlines():
        s = raw.rstrip("\n")
        if not s or s.lstrip().startswith("#"):
            lines.append(Line(kind="comment", text=raw))
            continue
        m = RULE_RE.match(s)
        if not m:
            lines.append(Line(kind="other", text=raw))
            continue
        t_raw, v_raw, p_raw = m.group(1), m.group(2), m.group(3)
        try:
            rtype = RuleType(t_raw)
        except Exception:
            lines.append(Line(kind="other", text=raw))
            continue
        policy = None
        if p_raw:
            try:
                policy = Policy(p_raw)
            except Exception:
                policy = None
        rule = Rule(type=rtype, value=v_raw.strip(), policy=policy)
        lines.append(Line(kind="rule", text=raw, rule=rule))
    return lines


def render_lines(lines: List[Line]) -> str:
    return "\n".join(_render_line(l) for l in lines) + "\n"


def _render_line(line: Line) -> str:
    if line.kind != "rule" or not line.rule:
        return line.text
    r = line.rule
    # Всегда рендерим без третьей колонки (policy)
    return f"{r.type.value},{r.value}"


def list_rules(lines: List[Line]) -> List[Tuple[int, Rule]]:
    return [(idx, l.rule) for idx, l in enumerate(lines) if l.kind == "rule" and l.rule is not None]


def find_rule_index(lines: List[Line], rtype: RuleType, value: str) -> Optional[int]:
    for idx, l in enumerate(lines):
        if l.kind == "rule" and l.rule and l.rule.type == rtype and l.rule.value == value:
            return idx
    return None


def add_rule(lines: List[Line], rule: Rule, added_comment: str) -> List[Line]:
    new_lines = list(lines)
    # Append comment and rule at file end
    new_lines.append(Line(kind="comment", text=added_comment))
    new_lines.append(Line(kind="rule", text="", rule=rule))
    return new_lines


def replace_policy(lines: List[Line], idx: int, new_policy: Policy) -> List[Line]:
    new_lines = list(lines)
    l = new_lines[idx]
    assert l.kind == "rule" and l.rule
    l.rule = Rule(type=l.rule.type, value=l.rule.value, policy=new_policy)
    return new_lines


def clear_policy(lines: List[Line], idx: int) -> List[Line]:
    """Remove policy (third column) for the given rule."""
    new_lines = list(lines)
    l = new_lines[idx]
    assert l.kind == "rule" and l.rule
    l.rule = Rule(type=l.rule.type, value=l.rule.value, policy=None)
    return new_lines


def delete_rule(lines: List[Line], idx: int, removed_comment: str | None = None) -> List[Line]:
    """Soft-delete a rule: keep it as a commented line and add a Removed marker.

    Behaviour:
    - If the previous line is an "# Added:" marker, replace it with the provided
      removed_comment (if any).
    - The rule line at idx is converted into a plain comment with the canonical
      rule text (two columns) so it is no longer active.
    - If there is no preceding Added marker and removed_comment is provided, the
      removed_comment is inserted directly above the commented rule.
    """
    new_lines = list(lines)
    if idx < 0 or idx >= len(new_lines):
        return new_lines

    l = new_lines[idx]
    if not (l.kind == "rule" and l.rule):
        return new_lines

    # Prepare commented rule text in two-column canonical form
    commented_text = f"# {rule_line(l.rule)}"

    prev = idx - 1
    if prev >= 0 and new_lines[prev].kind == "comment" and new_lines[prev].text.strip().startswith("# Added:"):
        # Replace the Added marker with Removed (if provided)
        if removed_comment:
            new_lines[prev] = Line(kind="comment", text=removed_comment)
        else:
            # Drop the Added marker if no replacement provided
            del new_lines[prev]
            idx -= 1  # our target line shifts one up
        # Convert the rule line into a comment (in-place, idx is valid after potential shift)
        new_lines[idx] = Line(kind="comment", text=commented_text)
    else:
        # No Added marker above: insert Removed (if provided) and comment out the rule
        new_lines[idx] = Line(kind="comment", text=commented_text)
        if removed_comment:
            new_lines.insert(idx, Line(kind="comment", text=removed_comment))
    return new_lines


def rule_line(rule: Rule) -> str:
    # Для сообщений и коммитов показываем формат файла (без политики)
    return f"{rule.type.value},{rule.value}"


def describe_rule(rule: Rule) -> str:
    type_map = {
        RuleType.DOMAIN_SUFFIX: "домен+поддомены",
        RuleType.DOMAIN: "точный домен",
        RuleType.DOMAIN_KEYWORD: "ключевое слово",
        RuleType.IP_CIDR: "IP-диапазон",
    }
    # Конфиг не требует третьей колонки, поэтому политику не показываем
    return f"{rule.value} ({type_map.get(rule.type)})"
