"""User-facing Telegram error handling."""

from __future__ import annotations

import html
import logging
import traceback
from dataclasses import dataclass

from telegram import Update
from telegram.error import BadRequest, Forbidden, NetworkError, TimedOut
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorGuide:
    title: str
    explanation: str
    next_steps: tuple[str, ...]


def support_code(error: BaseException) -> str:
    return hex(abs(hash((type(error).__name__, str(error)))) % 0xFFFFFF)[2:].upper().zfill(6)


def classify_error(error: BaseException) -> ErrorGuide:
    text = str(error).lower()

    if isinstance(error, (TimedOut, TimeoutError)) or "timeout" in text:
        return ErrorGuide(
            "Request timed out",
            "The market bot waited too long for Telegram, 0G RPC, storage, or compute provider data.",
            (
                "Retry the command in a minute.",
                "For provider lists, run /stack then retry.",
                "For uploads, try a smaller file first.",
            ),
        )

    if isinstance(error, NetworkError) or "connection" in text or "rpc" in text or "dns" in text:
        return ErrorGuide(
            "0G service connection issue",
            "The bot could not reach the 0G endpoint needed for this market action.",
            (
                "Run /stack to confirm the active endpoints.",
                "Retry after a short wait.",
                "If spending funds, run /my_resources and check your wallet balance before retrying.",
            ),
        )

    if isinstance(error, BadRequest):
        return ErrorGuide(
            "Telegram response formatting issue",
            "Telegram rejected the response, usually because it was too long or had invalid formatting.",
            (
                "Use a narrower command such as /compute_models or /storage_providers.",
                "Retry with shorter input for /estimate.",
                "If a provider list is large, retry later after the network response changes.",
            ),
        )

    if isinstance(error, Forbidden):
        return ErrorGuide(
            "Bot cannot reply here",
            "Telegram says the bot cannot send messages to this chat.",
            (
                "Open the bot directly and press Start.",
                "If this is a group, re-add the bot or allow messages.",
            ),
        )

    if isinstance(error, (ValueError, TypeError)) or "invalid" in text or "usage:" in text:
        return ErrorGuide(
            "Command format problem",
            "The command was missing an argument or one value had the wrong format.",
            (
                "Run /commands for exact syntax.",
                "Use /buy_storage <provider_id> <GB> [months].",
                "Use /buy_compute <provider_id> <hours>.",
            ),
        )

    if "insufficient" in text or "balance" in text or "fund" in text:
        return ErrorGuide(
            "Wallet funding issue",
            "The wallet needs more A0GI before this purchase or transaction can complete.",
            (
                "Use /start to view the wallet address.",
                "Fund it with A0GI on 0G mainnet.",
                "Retry the purchase after confirming the balance.",
            ),
        )

    if "provider" in text or "capacity" in text:
        return ErrorGuide(
            "Provider selection issue",
            "The selected provider was not found or does not have enough available capacity.",
            (
                "Run /storage_providers or /compute_providers again.",
                "Use the provider ID shown in the latest list.",
                "Lower the requested GB or compute hours and retry.",
            ),
        )

    if "storage" in text or "indexer" in text:
        return ErrorGuide(
            "0G Storage issue",
            "The storage upload or indexer request could not complete.",
            (
                "Retry /upload with a smaller file.",
                "Run /stack to confirm the storage indexer.",
                "Keep the file and retry when the indexer is reachable.",
            ),
        )

    if "compute" in text or "0g-compute" in text:
        return ErrorGuide(
            "0G Compute issue",
            "The compute discovery or purchase flow could not complete.",
            (
                "Run /compute_providers to refresh available routes.",
                "Run /compute_models to check model discovery.",
                "Retry after confirming the wallet has enough A0GI.",
            ),
        )

    return ErrorGuide(
        "Unexpected market bot error",
        "The command failed unexpectedly, but the bot is still running.",
        (
            "Retry the command once.",
            "Run /commands to confirm the right syntax.",
            "If it repeats, share the support code with the maintainer.",
        ),
    )


def format_error_message(error: BaseException, hint: str | None = None) -> str:
    guide = classify_error(error)
    code = support_code(error)
    lines = [
        f"<b>{html.escape(guide.title)}</b>",
        html.escape(guide.explanation),
        "",
        "<b>What to do next</b>",
    ]
    lines.extend(f"- {html.escape(step)}" for step in guide.next_steps)
    if hint:
        lines.extend(["", f"<b>Hint:</b> {html.escape(hint)}"])
    lines.extend(["", f"<b>Support code:</b> <code>{code}</code>"])
    return "\n".join(lines)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error or RuntimeError("Unknown error")
    code = support_code(error)
    logger.error(
        "Unhandled update error support_code=%s update=%r\n%s",
        code,
        update,
        "".join(traceback.format_exception(type(error), error, error.__traceback__)),
    )

    if not isinstance(update, Update):
        return
    store = context.application.bot_data.get("delivery_state_store")
    claimed_updates = context.application.bot_data.get("claimed_update_ids", set())
    if store is not None and update.update_id in claimed_updates:
        await store.mark_processed(update.update_id)
        claimed_updates.discard(update.update_id)
    target = update.effective_message
    try:
        if target:
            await target.reply_text(format_error_message(error), parse_mode="HTML")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text(format_error_message(error), parse_mode="HTML")
    except Exception:
        logger.exception("Failed to send user-facing error message support_code=%s", code)
