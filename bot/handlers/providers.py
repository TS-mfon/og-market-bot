from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.db.database import Database
from bot.services.provider_service import ProviderService
from bot.utils.formatting import Formatter


def register_provider_handlers(app, db: Database):
    svc = ProviderService(db)

    async def storage_providers_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        providers = await svc.list_providers("storage")
        if not providers:
            await update.message.reply_text("No storage providers available.")
            return
        text = "** 0G Storage Providers **\n\n"
        for p in providers:
            text += Formatter.provider_card(p) + "\n"
        text += "\nUse /buy_storage <provider_id> <GB> to purchase."
        await update.message.reply_text(text)

    async def compute_providers_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        providers = await svc.list_providers("compute")
        if not providers:
            await update.message.reply_text("No compute providers available.")
            return
        text = "** 0G Compute Providers **\n\n"
        for p in providers:
            text += Formatter.provider_card(p) + "\n"
        text += "\nUse /buy_compute <provider_id> <vCPU-hours> to purchase."
        await update.message.reply_text(text)

    app.add_handler(CommandHandler("storage_providers", storage_providers_cmd))
    app.add_handler(CommandHandler("compute_providers", compute_providers_cmd))
