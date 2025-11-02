import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.utils.logger import setup_logging
from bot.metrics import start_metrics_server
from bot.services.github_store import GitHubFileStore
from bot.handlers import start, add_rule, view_config, delete_rule
from bot.middlewares.access import AccessMiddleware
from bot.middlewares.logging import LoggingMiddleware


async def main() -> None:
    settings = get_settings()
    setup_logging(level=settings.log_level, json=settings.log_json)
    # Metrics
    start_metrics_server(settings.metrics_addr)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Shared services
    store = GitHubFileStore(settings)
    dp["store"] = store

    # Middlewares
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    dp.message.middleware(AccessMiddleware(settings.allowed_users))
    dp.callback_query.middleware(AccessMiddleware(settings.allowed_users))

    # Routers
    dp.include_routers(
        start.router,
        add_rule.router,
        view_config.router,
        delete_rule.router,
        # maintenance
        __import__("bot.handlers.normalize", fromlist=["router"]).router,
    )

    logging.info("Starting bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
