import logging
from typing import Optional

from bot.db.database import Database

logger = logging.getLogger(__name__)


class EarningsService:
    def __init__(self, db: Database):
        self.db = db

    async def get_earnings(self, telegram_id: int) -> dict:
        user = await self.db.get_user(telegram_id)
        if not user:
            return {"error": "User not found. Use /start first."}
        if not user.is_node_operator:
            return {"error": "You are not registered as a node operator."}

        summary = await self.db.get_earnings_summary(user.id)
        recent = await self.db.get_user_earnings(user.id)
        return {"summary": summary, "recent": recent}

    async def register_as_operator(
        self, telegram_id: int, node_address: str
    ) -> dict:
        user = await self.db.get_user(telegram_id)
        if not user:
            return {"success": False, "error": "User not found. Use /start first."}

        user.is_node_operator = True
        user.node_address = node_address
        await self.db.update_user(user)
        return {"success": True, "node_address": node_address}
