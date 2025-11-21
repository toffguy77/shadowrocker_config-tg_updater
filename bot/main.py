import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.utils.logger import setup_logging
from bot.metrics import start_metrics_server
from bot.services.github_store import GitHubFileStore
from bot.handlers import start, add_rule, view_config, delete_rule, cancel, url_check
from bot.middlewares.access import AccessMiddleware
from bot.middlewares.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    setup_logging(level=settings.log_level, json=settings.log_json)
    start_metrics_server(settings.metrics_addr)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    store = GitHubFileStore(settings)
    dp["store"] = store

    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(AccessMiddleware(settings.allowed_users))
    dp.callback_query.middleware(AccessMiddleware(settings.allowed_users))

    dp.include_routers(
        cancel.router,
        start.router,
        add_rule.router,
        view_config.router,
        delete_rule.router,
        url_check.router,
        __import__("bot.handlers.normalize", fromlist=["router"]).router,
    )

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Received shutdown signal")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    logger.info("Starting bot")
    try:
        polling_task = asyncio.create_task(dp.start_polling(bot))
        await stop_event.wait()
        polling_task.cancel()
        try:
            await asyncio.wait_for(polling_task, timeout=5.0)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("Polling task did not stop within timeout")
    finally:
        logger.info("Shutting down bot")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
