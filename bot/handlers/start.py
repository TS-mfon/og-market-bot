from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.db.database import Database
from bot.services.wallet_service import WalletService

BOT_COMMANDS = [
    ("start", "Create your wallet and show a quick overview"),
    ("commands", "List available bot commands"),
    ("help", "Show detailed usage help"),
    ("stack", "Show the 0G mainnet stack used by this bot"),
    ("storage_providers", "Browse storage providers"),
    ("compute_providers", "Browse compute providers"),
    ("compute_models", "List 0G Compute model catalog"),
    ("compare", "Compare providers side-by-side"),
    ("buy_storage", "Purchase storage capacity"),
    ("buy_compute", "Purchase compute capacity"),
    ("my_resources", "View active resources"),
    ("upload", "Upload a file to 0G storage"),
    ("files", "List your uploaded files"),
    ("job_status", "Check compute jobs"),
    ("earnings", "View node operator earnings"),
    ("estimate", "Estimate workload cost"),
]

WELCOME_TEXT = """
Welcome to the 0G Market Bot!

Your one-stop marketplace for 0G decentralized compute and storage.

What you can do:
  /stack             - Show the live 0G stack used by the bot
  /storage_providers - Browse storage providers
  /compute_providers - Browse compute providers
  /compute_models    - View 0G Compute model catalog
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
  /stack                    Show the live 0G stack used by the bot
  /storage_providers       List storage providers
  /compute_providers       List compute providers
  /compute_models          List 0G Compute models
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

COMMANDS_TEXT = """
0G Market Bot - Available Commands

/start - Create your wallet and show a quick overview
/commands - List available commands with short descriptions
/help - Show detailed usage help
/stack - Show the 0G mainnet stack used by this bot
/storage_providers - List storage providers
/compute_providers - List compute providers
/compute_models - List the 0G Compute model catalog
/compare <id1> <id2> - Compare providers
/buy_storage <id> <GB> [months] - Buy storage from a provider
/buy_compute <id> <hrs> - Buy compute from a provider
/estimate <description> - Estimate workload cost
/my_resources - View your active resources
/renew <resource_id> - Renew a resource
/cancel <resource_id> - Cancel a resource
/upload - Upload a file to 0G storage
/files - List uploaded files
/job_status - Check compute job status
/earnings - View node operator earnings
""".strip()


def register_start_handlers(app, db: Database):
    wallet_svc = WalletService(db)

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        tg_user = update.effective_user
        user = await wallet_svc.get_or_create_user(
            tg_user.id, tg_user.username
        )
        balance = await wallet_svc.get_balance(user.wallet_address)
        msg = (
            f"{WELCOME_TEXT}\n\n"
            f"Wallet: {user.wallet_address}\n"
            f"Balance: {balance:.4f} 0G"
        )
        await update.message.reply_text(msg)

    async def commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(COMMANDS_TEXT)

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(HELP_TEXT)

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("commands", commands_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
