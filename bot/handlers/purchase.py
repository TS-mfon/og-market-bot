from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from bot.db.database import Database
from bot.services.wallet_service import WalletService
from bot.services.purchase_service import PurchaseService
from bot.services.provider_service import ProviderService


def register_purchase_handlers(app, db: Database):
    wallet_svc = WalletService(db)
    purchase_svc = PurchaseService(db, wallet_svc)
    provider_svc = ProviderService(db)

    async def buy_storage_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        args = context.args or []
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /buy_storage <provider_id> <amount_GB> [months]\n"
                "Example: /buy_storage 1 100 3\n\n"
                "Use /storage_providers to see available providers."
            )
            return

        try:
            provider_id = int(args[0])
            amount_gb = float(args[1])
            months = int(args[2]) if len(args) > 2 else 1
        except ValueError:
            await update.message.reply_text(
                "Invalid arguments. Use numbers for provider_id, GB, and months."
            )
            return

        provider = await provider_svc.get_provider(provider_id)
        if not provider or provider.provider_type != "storage":
            await update.message.reply_text("Storage provider not found.")
            return

        total_price = provider.price_per_unit * amount_gb * months
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "Confirm Purchase",
                    callback_data=f"confirm_storage:{provider_id}:{amount_gb}:{months}",
                ),
                InlineKeyboardButton(
                    "Cancel", callback_data="cancel_purchase"
                ),
            ]
        ])

        await update.message.reply_text(
            f"Purchase Confirmation\n"
            f"{'=' * 30}\n"
            f"  Provider : {provider.name}\n"
            f"  Amount   : {amount_gb} GB\n"
            f"  Duration : {months} month(s)\n"
            f"  Price    : {total_price:.4f} 0G\n"
            f"{'=' * 30}\n"
            f"Proceed?",
            reply_markup=keyboard,
        )

    async def buy_compute_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        args = context.args or []
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /buy_compute <provider_id> <vCPU_hours>\n"
                "Example: /buy_compute 5 50\n\n"
                "Use /compute_providers to see available providers."
            )
            return

        try:
            provider_id = int(args[0])
            vcpu_hours = float(args[1])
        except ValueError:
            await update.message.reply_text(
                "Invalid arguments. Use numbers for provider_id and vCPU-hours."
            )
            return

        provider = await provider_svc.get_provider(provider_id)
        if not provider or provider.provider_type != "compute":
            await update.message.reply_text("Compute provider not found.")
            return

        total_price = provider.price_per_unit * vcpu_hours
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "Confirm Purchase",
                    callback_data=f"confirm_compute:{provider_id}:{vcpu_hours}",
                ),
                InlineKeyboardButton(
                    "Cancel", callback_data="cancel_purchase"
                ),
            ]
        ])

        await update.message.reply_text(
            f"Purchase Confirmation\n"
            f"{'=' * 30}\n"
            f"  Provider  : {provider.name}\n"
            f"  vCPU-hrs  : {vcpu_hours}\n"
            f"  Price     : {total_price:.4f} 0G\n"
            f"{'=' * 30}\n"
            f"Proceed?",
            reply_markup=keyboard,
        )

    async def confirm_callback(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "cancel_purchase":
            await query.edit_message_text("Purchase cancelled.")
            return

        telegram_id = query.from_user.id

        if data.startswith("confirm_storage:"):
            parts = data.split(":")
            provider_id = int(parts[1])
            amount_gb = float(parts[2])
            months = int(parts[3])

            await query.edit_message_text("Processing purchase...")
            result = await purchase_svc.purchase_storage(
                telegram_id, provider_id, amount_gb, months
            )

            if result["success"]:
                await query.edit_message_text(
                    f"Purchase Successful!\n\n"
                    f"  Resource ID : #{result['resource_id']}\n"
                    f"  Amount      : {result['amount']} GB\n"
                    f"  Paid        : {result['price']:.4f} 0G\n"
                    f"  Expires     : {result['expires_at']}\n"
                    f"  Tx          : {result['tx_hash'][:20]}...\n"
                    f"  Explorer    : {result['explorer_url']}\n\n"
                    f"Use /my_resources to view your resources."
                )
            else:
                await query.edit_message_text(f"Purchase failed: {result['error']}")

        elif data.startswith("confirm_compute:"):
            parts = data.split(":")
            provider_id = int(parts[1])
            vcpu_hours = float(parts[2])

            await query.edit_message_text("Processing purchase...")
            result = await purchase_svc.purchase_compute(
                telegram_id, provider_id, vcpu_hours
            )

            if result["success"]:
                await query.edit_message_text(
                    f"Purchase Successful!\n\n"
                    f"  Resource ID : #{result['resource_id']}\n"
                    f"  vCPU-hrs    : {result['amount']}\n"
                    f"  Paid        : {result['price']:.4f} 0G\n"
                    f"  Tx          : {result['tx_hash'][:20]}...\n"
                    f"  Explorer    : {result['explorer_url']}\n\n"
                    f"Use /my_resources to view your resources."
                )
            else:
                await query.edit_message_text(f"Purchase failed: {result['error']}")

    app.add_handler(CommandHandler("buy_storage", buy_storage_cmd))
    app.add_handler(CommandHandler("buy_compute", buy_compute_cmd))
    app.add_handler(
        CallbackQueryHandler(
            confirm_callback,
            pattern=r"^(confirm_storage|confirm_compute|cancel_purchase)",
        )
    )
