import logging
from typing import Optional

from bot.db.database import Database
from bot.models.resource import Resource
from bot.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class ResourceManager:
    def __init__(self, db: Database, wallet_service: WalletService):
        self.db = db
        self.wallet = wallet_service

    async def get_resources(
        self, telegram_id: int, status: Optional[str] = None
    ) -> list[Resource]:
        user = await self.db.get_user(telegram_id)
        if not user:
            return []
        return await self.db.get_user_resources(user.id, status)

    async def cancel_resource(self, telegram_id: int, resource_id: int) -> dict:
        user = await self.db.get_user(telegram_id)
        if not user:
            return {"success": False, "error": "User not found. Use /start first."}

        resources = await self.db.get_user_resources(user.id)
        resource = next((r for r in resources if r.id == resource_id), None)

        if not resource:
            return {"success": False, "error": "Resource not found."}
        if resource.status != "active":
            return {"success": False, "error": f"Resource is already {resource.status}."}

        await self.db.update_resource_status(resource_id, "cancelled")
        logger.info("Cancelled resource %d for user %d", resource_id, telegram_id)
        return {"success": True, "resource_id": resource_id}

    async def renew_resource(
        self, telegram_id: int, resource_id: int
    ) -> dict:
        user = await self.db.get_user(telegram_id)
        if not user:
            return {"success": False, "error": "User not found. Use /start first."}

        resources = await self.db.get_user_resources(user.id)
        resource = next((r for r in resources if r.id == resource_id), None)

        if not resource:
            return {"success": False, "error": "Resource not found."}

        provider = await self.db.get_provider(resource.provider_id)
        if not provider:
            return {"success": False, "error": "Provider no longer available."}

        renew_price = provider.price_per_unit * resource.amount
        balance = self.wallet.get_balance(user.wallet_address)

        if balance < renew_price:
            return {
                "success": False,
                "error": (
                    f"Insufficient balance for renewal. "
                    f"Need {renew_price:.4f} 0G, have {balance:.4f} 0G.\n"
                    f"Deposit to: {user.wallet_address}"
                ),
            }

        try:
            pk = self.wallet.get_private_key(user)
            tx_hash = self.wallet.send_transaction(
                pk, provider.address, renew_price
            )
        except Exception as e:
            logger.error("Renewal tx failed: %s", e)
            return {"success": False, "error": f"Transaction failed: {e}"}

        await self.db.update_resource_status(resource_id, "active")
        return {
            "success": True,
            "resource_id": resource_id,
            "price": renew_price,
            "tx_hash": tx_hash,
            "explorer_url": self.wallet.get_explorer_url(tx_hash),
        }
