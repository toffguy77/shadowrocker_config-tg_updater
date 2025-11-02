import logging
import os
from logging import Logger

try:
    from pythonjsonlogger import jsonlogger
except Exception:  # pragma: no cover
    jsonlogger = None  # type: ignore


def setup_logging(level: str = "INFO", json: bool = True) -> None:
    lvl = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(lvl)

    handler = logging.StreamHandler()
    if json and jsonlogger is not None:
        fmt = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(filename)s %(lineno)d",
            json_ensure_ascii=False,
        )
        handler.setFormatter(fmt)
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        handler.setFormatter(formatter)
    root.addHandler(handler)


def get_logger(name: str) -> Logger:
    return logging.getLogger(name)
