from enum import Enum


class RuleType(str, Enum):
    DOMAIN_SUFFIX = "DOMAIN-SUFFIX"
    DOMAIN = "DOMAIN"
    DOMAIN_KEYWORD = "DOMAIN-KEYWORD"
    IP_CIDR = "IP-CIDR"


class Policy(str, Enum):
    PROXY = "PROXY"
    DIRECT = "DIRECT"
    REJECT = "REJECT"
