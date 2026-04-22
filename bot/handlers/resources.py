from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from bot.db.database import Database
from bot.services.wallet_service import WalletService
from bot.services.resource_manager import ResourceManager
from bot.utils.formatting import Formatter


def register_resource_handlers(app, db: Database):
    wallet_svc = WalletService(db)
    res_mgr = ResourceManager(db, wallet_svc)

    async def my_resources_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        telegram_id = update.effective_user.id
        resources = await res_mgr.get_resources(telegram_id)

        if not resources:
            await update.message.reply_text(
                "You have no resources yet.\n"
                "Use /buy_storage or /buy_compute to get started."
            )
            return

        text = "Your Resources\n" + "=" * 30 + "\n\n"
        for r in resources:
            provider = await db.get_provider(r.provider_id)
            pname = provider.name if provider else "Unknown"
            text += Formatter.resource_card(r, pname) + "\n\n"

        text += (
            "Actions:\n"
            "  /renew <id>   - Renew a resource\n"
            "  /cancel <id>  - Cancel a resource"
        )
        await update.message.reply_text(text)

    async def renew_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args or []
        if not args:
            await update.message.reply_text(
                "Usage: /renew <resource_id>\n"
                "Use /my_resources to see your resource IDs."
            )
            return

        try:
            resource_id = int(args[0])
        except ValueError:
            await update.message.reply_text("Invalid resource ID.")
            return

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "Confirm Renewal",
                    callback_data=f"renew_confirm:{resource_id}",
                ),
                InlineKeyboardButton(
                    "Cancel", callback_data="renew_cancel"
                ),
            ]
        ])
        await update.message.reply_text(
            f"Renew resource #{resource_id}?", reply_markup=keyboard
        )

    async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args or []
        if not args:
            await update.message.reply_text(
                "Usage: /cancel <resource_id>\n"
                "Use /my_resources to see your resource IDs."
            )
            return

        try:
            resource_id = int(args[0])
        except ValueError:
            await update.message.reply_text("Invalid resource ID.")
            return

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "Confirm Cancel",
                    callback_data=f"cancel_confirm:{resource_id}",
                ),
                InlineKeyboardButton(
                    "Keep", callback_data="cancel_abort"
                ),
            ]
        ])
        await update.message.reply_text(
            f"Cancel resource #{resource_id}? This cannot be undone.",
            reply_markup=keyboard,
        )

    async def resource_callback(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()
        data = query.data
        telegram_id = query.from_user.id

        if data == "renew_cancel" or data == "cancel_abort":
            await query.edit_message_text("Action cancelled.")
            return

        if data.startswith("renew_confirm:"):
            resource_id = int(data.split(":")[1])
            result = await res_mgr.renew_resource(telegram_id, resource_id)
            if result["success"]:
                await query.edit_message_text(
                    f"Resource #{resource_id} renewed!\n"
                    f"  Paid: {result['price']:.4f} 0G\n"
                    f"  Tx: {result['tx_hash'][:20]}...\n"
                    f"  Explorer: {result['explorer_url']}"
                )
            else:
                await query.edit_message_text(
                    f"Renewal failed: {result['error']}"
                )

        elif data.startswith("cancel_confirm:"):
            resource_id = int(data.split(":")[1])
            result = await res_mgr.cancel_resource(telegram_id, resource_id)
            if result["success"]:
                await query.edit_message_text(
                    f"Resource #{resource_id} has been cancelled."
                )
            else:
                await query.edit_message_text(
                    f"Cancel failed: {result['error']}"
                )

    app.add_handler(CommandHandler("my_resources", my_resources_cmd))
    app.add_handler(CommandHandler("renew", renew_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(
        CallbackQueryHandler(
            resource_callback,
            pattern=r"^(renew_confirm|renew_cancel|cancel_confirm|cancel_abort)",
        )
    )
