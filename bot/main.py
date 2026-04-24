"""0G Market Bot - entry point."""

import logging
import os

from telegram import BotCommand
from telegram.ext import Application

from bot.config import config
from bot.db.database import Database
from bot.handlers import register_all_handlers
from bot.handlers.start import BOT_COMMANDS
from bot.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    db: Database = application.bot_data["db"]
    await db.connect()
    await application.bot.set_my_commands(
        [BotCommand(command, description) for command, description in BOT_COMMANDS]
    )
    logger.info("Database initialized")


async def post_shutdown(application: Application) -> None:
    db: Database = application.bot_data["db"]
    await db.close()
    logger.info("Database closed")


def _webhook_base_url() -> str:
    return config.WEBHOOK_BASE_URL.strip() or os.environ.get("RENDER_EXTERNAL_URL", "").strip()


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    db = Database()

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.bot_data["db"] = db

    register_all_handlers(app, db)

    logger.info("Starting 0G Market Bot...")
    webhook_base = _webhook_base_url()
    if webhook_base:
        token = config.TELEGRAM_BOT_TOKEN
        url_path = f"/telegram/{token}"
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", "10000")),
            url_path=url_path,
            webhook_url=f"{webhook_base}{url_path}",
            drop_pending_updates=True,
        )
        return

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
