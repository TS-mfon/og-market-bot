from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from bot.db.database import Database
from bot.services.wallet_service import WalletService
from bot.services.storage_service import StorageService
from bot.utils.formatting import Formatter


def register_upload_handlers(app, db: Database):
    wallet_svc = WalletService(db)
    storage_svc = StorageService(db, wallet_svc)

    async def upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Send me a file and I will upload it to 0G storage.\n\n"
            "Supported: any file type, up to 20 MB."
        )

    async def handle_document(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        document = update.message.document
        if not document:
            return

        if document.file_size > 20 * 1024 * 1024:
            await update.message.reply_text(
                "File too large. Maximum size is 20 MB."
            )
            return

        status_msg = await update.message.reply_text(
            f"Uploading {document.file_name} ({document.file_size / 1024:.1f} KB)..."
        )

        tg_file = await context.bot.get_file(document.file_id)
        file_bytes = await tg_file.download_as_bytearray()

        result = await storage_svc.upload_file(
            update.effective_user.id,
            document.file_name,
            bytes(file_bytes),
        )

        if result["success"]:
            text = (
                f"File uploaded successfully!\n\n"
                f"  File ID    : #{result['file_id']}\n"
                f"  Name       : {result['filename']}\n"
                f"  Size       : {result['size'] / 1024:.1f} KB\n"
                f"  Merkle Root: {result['merkle_root'][:24]}...\n"
            )
            if result.get("tx_hash"):
                text += f"  Tx         : {result['tx_hash'][:20]}...\n"
            if result.get("note"):
                text += f"\n  Note: {result['note']}\n"
            text += "\nUse /files to see all your files."
            await status_msg.edit_text(text)
        else:
            await status_msg.edit_text(
                f"Upload failed: {result.get('error', 'Unknown error')}"
            )

    async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        files = await storage_svc.list_files(update.effective_user.id)
        if not files:
            await update.message.reply_text(
                "No files yet. Use /upload or send a file to get started."
            )
            return

        text = "Your Files\n" + "=" * 30 + "\n\n"
        for f in files:
            text += Formatter.file_card(f) + "\n"
        await update.message.reply_text(text)

    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(
        MessageHandler(filters.Document.ALL, handle_document)
    )
