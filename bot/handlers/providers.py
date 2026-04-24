import html

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.config import config
from bot.db.database import Database
from bot.services.og_compute_cli import (
    get_network_status,
    list_compute_providers,
    list_model_catalog,
)
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
        text = (
            "0G Storage Mainnet\n\n"
            f"Indexer: {config.OG_STORAGE_INDEXER}\n"
            f"Explorer: {config.OG_EXPLORER}\n"
            f"Purchase route contract: {config.OG_MARKET_HUB_ADDRESS or 'not configured'}\n\n"
            "Bot purchase routes\n\n"
        )
        for p in providers:
            text += Formatter.provider_card(p) + "\n"
        text += "\nUse /buy_storage <provider_id> <GB> to purchase."
        await update.message.reply_text(text)

    async def compute_providers_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        providers = await svc.list_providers("compute")
        parts = []
        try:
            network = await get_network_status()
            live = await list_compute_providers()
            parts.append(f"0G Compute network\n\n<pre>{html.escape(network[:1200])}</pre>")
            parts.append(f"Live compute providers\n\n<pre>{html.escape(live[:2000])}</pre>")
        except Exception as exc:
            parts.append(f"Live compute discovery unavailable right now: {exc}")
        text = "\n\n".join(parts) + "\n\nBot purchase routes\n\n"
        for p in providers:
            text += Formatter.provider_card(p) + "\n"
        text += "\nUse /buy_compute <provider_id> <vCPU-hours> to purchase."
        await update.message.reply_text(text, parse_mode="HTML")

    async def compute_models_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        try:
            models = await list_model_catalog()
            await update.message.reply_text(
                f"0G Compute model catalog\n\n<pre>{html.escape(models[:3500])}</pre>",
                parse_mode="HTML",
            )
        except Exception as exc:
            await update.message.reply_text(f"Could not load model catalog: {exc}")

    async def stack_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        lines = [
            "0G stack used by 0G Market Bot",
            "",
            f"Chain RPC: {config.OG_RPC_URL}",
            f"Chain ID: {config.OG_CHAIN_ID}",
            f"Explorer: {config.OG_EXPLORER}",
            f"Storage Indexer: {config.OG_STORAGE_INDEXER}",
            f"Compute CLI network: {config.OG_COMPUTE_CLI_NETWORK}",
            f"Market contract: {config.OG_MARKET_HUB_ADDRESS or 'not configured'}",
        ]
        await update.message.reply_text("\n".join(lines))

    app.add_handler(CommandHandler("storage_providers", storage_providers_cmd))
    app.add_handler(CommandHandler("compute_providers", compute_providers_cmd))
    app.add_handler(CommandHandler("compute_models", compute_models_cmd))
    app.add_handler(CommandHandler("stack", stack_cmd))
