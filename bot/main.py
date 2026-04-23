"""0G Market Bot - entry point."""

import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram.ext import Application

from bot.config import config
from bot.db.database import Database
from bot.handlers import register_all_handlers
from bot.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    db: Database = application.bot_data["db"]
    await db.connect()
    logger.info("Database initialized")


async def post_shutdown(application: Application) -> None:
    db: Database = application.bot_data["db"]
    await db.close()
    logger.info("Database closed")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok","bot":"og-market"}')

    def log_message(self, *args):
        pass  # suppress


def start_health_server():
    port = int(os.environ.get("PORT", 10000))
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

    register_all_handlers(app, db)

    logger.info("Starting 0G Market Bot...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    # Start health server BEFORE main (which blocks on polling)
    threading.Thread(target=start_health_server, daemon=True).start()
    main()
