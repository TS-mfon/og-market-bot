import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from bot.db.database import Database
from bot.models.resource import Resource
from bot.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class PurchaseService:
    def __init__(self, db: Database, wallet_service: WalletService):
        self.db = db
        self.wallet = wallet_service

    async def purchase_storage(
        self,
        telegram_id: int,
        provider_id: int,
        amount_gb: float,
        duration_months: int = 1,
    ) -> dict:
        user = await self.wallet.get_or_create_user(telegram_id)
        provider = await self.db.get_provider(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not found"}
        if provider.provider_type != "storage":
            return {"success": False, "error": "Not a storage provider"}
        if amount_gb > provider.available_capacity:
            return {
                "success": False,
                "error": f"Not enough capacity. Available: {provider.available_capacity:.0f} GB",
            }

        total_price = provider.price_per_unit * amount_gb * duration_months
        balance = self.wallet.get_balance(user.wallet_address)

        if balance < total_price:
            return {
                "success": False,
                "error": (
                    f"Insufficient balance. Need {total_price:.4f} 0G, "
                    f"have {balance:.4f} 0G.\n"
                    f"Deposit to: {user.wallet_address}"
                ),
            }

        # Send payment on-chain
        try:
            pk = self.wallet.get_private_key(user)
            tx_hash = self.wallet.send_transaction(
                pk, provider.address, total_price
            )
        except Exception as e:
            logger.error("Purchase tx failed: %s", e)
            return {"success": False, "error": f"Transaction failed: {e}"}

        expires = datetime.utcnow() + timedelta(days=30 * duration_months)
        resource = Resource(
            user_id=user.id,
            resource_type="storage",
            provider_id=provider_id,
            amount=amount_gb,
            price_paid=total_price,
            tx_hash=tx_hash,
            status="active",
            expires_at=expires.isoformat(),
            metadata=json.dumps({"duration_months": duration_months}),
        )
        resource.id = await self.db.create_resource(resource)

        return {
            "success": True,
            "resource_id": resource.id,
            "amount": amount_gb,
            "price": total_price,
            "tx_hash": tx_hash,
            "expires_at": expires.isoformat(),
            "explorer_url": self.wallet.get_explorer_url(tx_hash),
        }

    async def purchase_compute(
        self,
        telegram_id: int,
        provider_id: int,
        vcpu_hours: float,
    ) -> dict:
        user = await self.wallet.get_or_create_user(telegram_id)
        provider = await self.db.get_provider(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not found"}
        if provider.provider_type != "compute":
            return {"success": False, "error": "Not a compute provider"}
        if vcpu_hours > provider.available_capacity:
            return {
                "success": False,
                "error": f"Not enough capacity. Available: {provider.available_capacity:.0f} vCPU-hrs",
            }

        total_price = provider.price_per_unit * vcpu_hours
        balance = self.wallet.get_balance(user.wallet_address)

        if balance < total_price:
            return {
                "success": False,
                "error": (
                    f"Insufficient balance. Need {total_price:.4f} 0G, "
                    f"have {balance:.4f} 0G.\n"
                    f"Deposit to: {user.wallet_address}"
                ),
            }

        try:
            pk = self.wallet.get_private_key(user)
            tx_hash = self.wallet.send_transaction(
                pk, provider.address, total_price
            )
        except Exception as e:
            logger.error("Purchase tx failed: %s", e)
            return {"success": False, "error": f"Transaction failed: {e}"}

        resource = Resource(
            user_id=user.id,
            resource_type="compute",
            provider_id=provider_id,
            amount=vcpu_hours,
            price_paid=total_price,
            tx_hash=tx_hash,
            status="active",
            metadata=json.dumps({"vcpu_hours": vcpu_hours}),
        )
        resource.id = await self.db.create_resource(resource)

        return {
            "success": True,
            "resource_id": resource.id,
            "amount": vcpu_hours,
            "price": total_price,
            "tx_hash": tx_hash,
            "explorer_url": self.wallet.get_explorer_url(tx_hash),
        }
