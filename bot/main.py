"""0G Market Bot - entry point."""

import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import BotCommand, Update
from telegram.ext import Application, TypeHandler

from bot.config import config
from bot.db.database import Database
from bot.handlers import register_all_handlers
from bot.handlers.start import BOT_COMMANDS
from bot.utils.errors import error_handler
from bot.utils.failover import (
    degraded_runtime_notice_handler,
    duplicate_guard_handler,
    finalize_update_handler,
    install_failover,
    runtime_health_payload,
    shutdown_failover,
)
from bot.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    db: Database = application.bot_data["db"]
    await db.connect()
    await install_failover(application, "og-market-bot", "0G Market Bot")
    await application.bot.set_my_commands(
        [BotCommand(command, description) for command, description in BOT_COMMANDS]
    )
    logger.info("Database initialized")


async def post_shutdown(application: Application) -> None:
    await shutdown_failover(application)
    db: Database = application.bot_data["db"]
    await db.close()
    logger.info("Database closed")


def _webhook_base_url() -> str:
    return config.WEBHOOK_BASE_URL.strip() or os.environ.get("RENDER_EXTERNAL_URL", "").strip()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        payload = runtime_health_payload("og-market-bot", "0G Market Bot")
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def log_message(self, *args):
        pass


def start_health_server() -> None:
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


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

    app.add_handler(TypeHandler(Update, duplicate_guard_handler), group=-100)
    app.add_handler(TypeHandler(Update, degraded_runtime_notice_handler), group=-90)
    register_all_handlers(app, db)
    app.add_handler(TypeHandler(Update, finalize_update_handler), group=1000)
    app.add_error_handler(error_handler)

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

    threading.Thread(target=start_health_server, daemon=True).start()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
