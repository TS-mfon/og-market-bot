from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.db.database import Database
from bot.services.provider_service import ProviderService


def register_estimate_handlers(app, db: Database):
    svc = ProviderService(db)

    async def estimate_cmd(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        args = context.args or []
        if not args:
            await update.message.reply_text(
                "Usage: /estimate <workload description>\n\n"
                "Examples:\n"
                "  /estimate store 500 GB of backups\n"
                "  /estimate run ML training for 24 hours\n"
                "  /estimate 100 GB storage and 10 hours compute"
            )
            return

        description = " ".join(args)
        est = svc.estimate_cost(description)

        lines = [
            "Cost Estimate",
            "=" * 30,
            f"  Description : {description}",
            "",
        ]

        if est["storage_gb"] > 0:
            lines.append(f"  Storage     : {est['storage_gb']:.1f} GB")
            lines.append(f"  Storage cost: {est['storage_cost']:.4f} 0G")

        if est["compute_hours"] > 0:
            lines.append(f"  Compute     : {est['compute_hours']:.1f} vCPU-hrs")
            lines.append(f"  Compute cost: {est['compute_cost']:.4f} 0G")

        lines += [
            "",
            f"  TOTAL       : {est['total_cost']:.4f} 0G",
            "=" * 30,
            "",
            "Note: Estimates use average provider pricing.",
            "Use /compare for exact per-provider rates.",
        ]

        await update.message.reply_text("\n".join(lines))

    app.add_handler(CommandHandler("estimate", estimate_cmd))
