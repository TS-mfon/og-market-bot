from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.db.database import Database
from bot.services.earnings_service import EarningsService
from bot.utils.formatting import Formatter


def register_earnings_handlers(app, db: Database):
    earnings_svc = EarningsService(db)

    async def earnings_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        telegram_id = update.effective_user.id
        args = context.args or []

        # Allow registering as node operator: /earnings register <node_address>
        if args and args[0].lower() == "register":
            if len(args) < 2:
                await update.message.reply_text(
                    "Usage: /earnings register <node_address>\n"
                    "Register your 0G node address to track earnings."
                )
                return
            node_addr = args[1]
            result = await earnings_svc.register_as_operator(
                telegram_id, node_addr
            )
            if result["success"]:
                await update.message.reply_text(
                    f"Registered as node operator!\n"
                    f"Node address: {result['node_address']}\n\n"
                    f"Use /earnings to view your earnings."
                )
            else:
                await update.message.reply_text(
                    f"Registration failed: {result['error']}"
                )
            return

        result = await earnings_svc.get_earnings(telegram_id)
        if "error" in result:
            if "not registered" in result["error"].lower():
                await update.message.reply_text(
                    f"{result['error']}\n\n"
                    f"Register with: /earnings register <node_address>"
                )
            else:
                await update.message.reply_text(result["error"])
            return

        text = Formatter.earnings_summary(result["summary"], result["recent"])
        await update.message.reply_text(text)

    app.add_handler(CommandHandler("earnings", earnings_cmd))
