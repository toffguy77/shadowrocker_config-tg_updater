from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class AccessMiddleware(BaseMiddleware):
    def __init__(self, allowed_users: list[int] | None = None) -> None:
        super().__init__()
        self.allowed = set(allowed_users or [])

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: dict[str, Any]) -> Any:
        if not self.allowed:
            return await handler(event, data)
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        if user_id and user_id in self.allowed:
            return await handler(event, data)
        # deny with feedback
        if isinstance(event, Message):
            await event.answer("Доступ ограничен. Обратитесь к администратору.")
        elif isinstance(event, CallbackQuery):
            try:
                await event.answer("Доступ ограничен", show_alert=True)
            except Exception:
                pass
        return
