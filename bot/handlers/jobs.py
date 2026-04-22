from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.db.database import Database
from bot.utils.formatting import Formatter


def register_job_handlers(app, db: Database):

    async def job_status_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        telegram_id = update.effective_user.id
        user = await db.get_user(telegram_id)
        if not user:
            await update.message.reply_text(
                "You haven't started yet. Use /start first."
            )
            return

        jobs = await db.get_user_jobs(user.id)
        if not jobs:
            await update.message.reply_text(
                "No compute jobs found.\n"
                "Purchase compute resources with /buy_compute to run jobs."
            )
            return

        text = "Compute Jobs\n" + "=" * 30 + "\n\n"
        for j in jobs:
            text += Formatter.job_card(j) + "\n\n"
        await update.message.reply_text(text)

    app.add_handler(CommandHandler("job_status", job_status_cmd))
