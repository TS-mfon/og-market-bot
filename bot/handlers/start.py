from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.db.database import Database
from bot.services.wallet_service import WalletService

WELCOME_TEXT = """
Welcome to the 0G Market Bot!

Your one-stop marketplace for 0G decentralized compute and storage.

What you can do:
  /storage_providers - Browse storage providers
  /compute_providers - Browse compute providers
  /compare           - Compare providers side-by-side
  /buy_storage       - Purchase storage
  /buy_compute       - Purchase compute
  /my_resources      - View your resources
  /upload            - Upload a file to 0G storage
  /files             - List your uploaded files
  /job_status        - Check compute job status
  /earnings          - Node operator earnings
  /estimate          - Estimate costs for a workload
  /help              - Show this help message

Your embedded wallet has been created automatically.
""".strip()

HELP_TEXT = """
0G Market Bot - Commands

BROWSING
  /storage_providers       List storage providers
  /compute_providers       List compute providers
  /compare <id1> <id2>     Compare providers

PURCHASING
  /buy_storage <id> <GB>   Buy storage from provider
  /buy_compute <id> <hrs>  Buy compute from provider
  /estimate <description>  Estimate workload cost

RESOURCES
  /my_resources            View your active resources
  /renew <resource_id>     Renew a resource
  /cancel <resource_id>    Cancel a resource

STORAGE
  /upload                  Upload a file (send file after)
  /files                   List your uploaded files

COMPUTE
  /job_status              View compute job statuses

EARNINGS
  /earnings                View node operator earnings

WALLET
  Your wallet is created on /start.
  Fund it to make purchases on the 0G network.
""".strip()


def register_start_handlers(app, db: Database):
    wallet_svc = WalletService(db)

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        tg_user = update.effective_user
        user = await wallet_svc.get_or_create_user(
            tg_user.id, tg_user.username
        )
        balance = wallet_svc.get_balance(user.wallet_address)
        msg = (
            f"{WELCOME_TEXT}\n\n"
            f"Wallet: {user.wallet_address}\n"
            f"Balance: {balance:.4f} 0G"
        )
        await update.message.reply_text(msg)

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(HELP_TEXT)

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
