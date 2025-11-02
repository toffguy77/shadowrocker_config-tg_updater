import ipaddress
from typing import Tuple


def normalize_ip(raw: str) -> Tuple[bool, str]:
    s = raw.strip()
    if '/' not in s:
        s = f"{s}/32"
    try:
        net = ipaddress.ip_network(s, strict=False)
        if net.version != 4:
            return False, "Только IPv4 поддерживается."
        if not (0 <= net.prefixlen <= 32):
            return False, "Маска подсети должна быть 0..32."
        return True, f"{net.network_address}/{net.prefixlen}"
    except Exception:
        return False, "Некорректный IP-адрес или диапазон (ожидается IPv4 или IPv4/CIDR)."
