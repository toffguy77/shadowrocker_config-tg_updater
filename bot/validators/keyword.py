import re
from typing import Tuple

KW_RE = re.compile(r"^[a-z0-9-]{2,50}$")


def normalize_keyword(raw: str) -> Tuple[bool, str]:
    s = raw.strip().lower()
    if not KW_RE.match(s):
        return False, (
            "Ключевое слово: 2–50 символов, только латиница/цифры/дефис, без пробелов."
        )
    return True, s
