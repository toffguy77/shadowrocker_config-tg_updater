import logging
from typing import Optional

from prometheus_client import Counter, Histogram, start_http_server

# Counters
RULES_ADDED = Counter("rules_added_total", "Number of rules added")
RULES_REPLACED = Counter("rules_replaced_total", "Number of rules replaced (policy changed)")
RULES_DELETED = Counter("rules_deleted_total", "Number of rules deleted")
INPUT_VALID = Counter("input_valid_total", "Valid user inputs")
INPUT_INVALID = Counter("input_invalid_total", "Invalid user inputs")
GITHUB_ERRORS = Counter("github_errors_total", "GitHub API errors")

# Histograms
GITHUB_FETCH_SECONDS = Histogram(
    "github_fetch_seconds",
    "Time spent fetching file from GitHub",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
GITHUB_COMMIT_SECONDS = Histogram(
    "github_commit_seconds",
    "Time spent committing file to GitHub",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


def start_metrics_server(addr: str) -> None:
    host, _, port_str = addr.partition(":")
    host = host or "0.0.0.0"
    port = int(port_str or 9123)
    logging.getLogger(__name__).info("Starting Prometheus metrics server", extra={"host": host, "port": port})
    start_http_server(port, addr=host)
