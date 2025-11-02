import re
from urllib.parse import urlparse
from typing import Tuple

try:
    from publicsuffix2 import get_sld  # type: ignore
except Exception:  # pragma: no cover
    get_sld = None  # fallback later

DOMAIN_RE = re.compile(r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")

_COMMON_MULTI_TLD = {"co.uk", "com.au", "co.jp", "com.br", "com.cn", "co.in", "co.za"}


def _clean_host(raw: str) -> str:
    s = raw.strip()
    if "://" in s:
        p = urlparse(s)
        host = p.netloc or p.path  # some invalid cases
    else:
        host = s
    # strip path if present accidentally
    if "/" in host:
        host = host.split("/")[0]
    # strip query
    if "?" in host:
        host = host.split("?")[0]
    # strip port
    if ":" in host:
        host = host.split(":")[0]
    host = host.strip().strip(".")
    return host.lower()


def _registrable_domain(host: str) -> str:
    if get_sld:
        sld = get_sld(host)
        if sld:
            return sld.lower()
    # heuristic fallback
    parts = host.split('.')
    if len(parts) >= 3:
        last2 = ".".join(parts[-2:])
        last3 = ".".join(parts[-3:])
        if last2 in _COMMON_MULTI_TLD and len(parts) >= 3:
            return last3
        return last2
    return host


def normalize_domain_suffix(raw: str) -> Tuple[bool, str]:
    host = _clean_host(raw)
    if len(host) < 3 or len(host) > 253:
        return False, (
            "Не удалось распознать домен. Проверьте: латиница/цифры/.-, длина 3-253, должен содержать точку (example.com)."
        )
    if any(len(label) > 63 for label in host.split('.')):
        return False, "Метка домена не может быть длиннее 63 символов."
    if not DOMAIN_RE.match(host):
        return False, (
            "Не удалось распознать домен. Проверьте: латиница/цифры/.-, длина 3-253, должен содержать точку (example.com)."
        )
    base = _registrable_domain(host)
    return True, base


def normalize_domain_exact(raw: str) -> Tuple[bool, str]:
    host = _clean_host(raw)
    if len(host) < 3 or len(host) > 253:
        return False, (
            "Не удалось распознать домен. Проверьте: латиница/цифры/.-, длина 3-253, должен содержать точку (example.com)."
        )
    if any(len(label) > 63 for label in host.split('.')):
        return False, "Метка домена не может быть длиннее 63 символов."
    if not DOMAIN_RE.match(host):
        return False, (
            "Не удалось распознать домен. Проверьте: латиница/цифры/.-, длина 3-253, должен содержать точку (example.com)."
        )
    return True, host
