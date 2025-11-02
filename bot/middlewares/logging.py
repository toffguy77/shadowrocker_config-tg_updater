from typing import Callable, Awaitable, Any
import time
import logging

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger = logging.getLogger("tg")
        start = time.perf_counter()
        kind = type(event).__name__
        user_id = None
        username = None
        text = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            username = event.from_user.username if event.from_user else None
            text = event.text
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            username = event.from_user.username if event.from_user else None
            text = event.data
        try:
            result = await handler(event, data)
            elapsed = time.perf_counter() - start
            logger.info(
                "handled",
                extra={
                    "kind": kind,
                    "user_id": user_id,
                    "username": username,
                    "payload": text,
                    "elapsed_ms": int(elapsed * 1000),
                },
            )
            return result
        except Exception as e:  # noqa: BLE001
            elapsed = time.perf_counter() - start
            logger.exception(
                "error",
                extra={
                    "kind": kind,
                    "user_id": user_id,
                    "username": username,
                    "payload": text,
                    "elapsed_ms": int(elapsed * 1000),
                },
            )
            raise
