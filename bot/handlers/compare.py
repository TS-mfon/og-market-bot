from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.db.database import Database
from bot.services.provider_service import ProviderService
from bot.utils.formatting import Formatter


def register_compare_handlers(app, db: Database):
    svc = ProviderService(db)

    async def compare_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        args = context.args or []

        if not args:
            # Compare all storage or all compute
            storage = await svc.list_providers("storage")
            compute = await svc.list_providers("compute")
            text = ""
            if storage:
                text += Formatter.provider_comparison_table(storage) + "\n"
            if compute:
                text += Formatter.provider_comparison_table(compute)
            if not text:
                text = "No providers available."
            await update.message.reply_text(text, parse_mode="HTML")
            return

        # Compare specific provider IDs
        try:
            ids = [int(a) for a in args]
        except ValueError:
            await update.message.reply_text(
                "Usage: /compare [provider_id1] [provider_id2] ...\n"
                "Or just /compare to see all providers."
            )
            return

        providers = await svc.compare_providers(ids)
        if not providers:
            await update.message.reply_text("No matching providers found.")
            return

        # Group by type
        storage = [p for p in providers if p.provider_type == "storage"]
        compute = [p for p in providers if p.provider_type == "compute"]

        text = ""
        if storage:
            text += Formatter.provider_comparison_table(storage) + "\n"
        if compute:
            text += Formatter.provider_comparison_table(compute)

        await update.message.reply_text(text or "No providers found.", parse_mode="HTML")

    app.add_handler(CommandHandler("compare", compare_cmd))
