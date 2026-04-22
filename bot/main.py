import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import logging

from telegram.ext import Application

from bot.config import config
from bot.db.database import Database
from bot.handlers import register_all_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Called after the Application has been initialized."""
    db: Database = application.bot_data["db"]
    await db.connect()
    logger.info("Database initialized")


async def post_shutdown(application: Application) -> None:
    """Called when the Application is shutting down."""
    db: Database = application.bot_data["db"]
    await db.close()
    logger.info("Database closed")


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")

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
    main()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok","bot":"og-market"}')
    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# Start health server for Render
threading.Thread(target=start_health_server, daemon=True).start()
