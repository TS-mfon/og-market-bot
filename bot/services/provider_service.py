import logging
from typing import Optional

from bot.db.database import Database
from bot.models.provider import Provider

logger = logging.getLogger(__name__)


class ProviderService:
    def __init__(self, db: Database):
        self.db = db

    async def list_providers(
        self, provider_type: Optional[str] = None
    ) -> list[Provider]:
        return await self.db.get_providers(provider_type)

    async def get_provider(self, provider_id: int) -> Optional[Provider]:
        return await self.db.get_provider(provider_id)

    async def compare_providers(
        self, provider_ids: list[int]
    ) -> list[Provider]:
        providers = []
        for pid in provider_ids:
            p = await self.db.get_provider(pid)
            if p:
                providers.append(p)
        return providers

    def estimate_cost(self, description: str) -> dict:
        """Parse a natural-language workload description and estimate cost."""
        desc = description.lower()

        storage_gb = 0.0
        compute_hours = 0.0

        # Storage keywords
        if any(w in desc for w in ["store", "storage", "save", "backup", "archive"]):
            storage_gb = 10.0  # default
            for token in desc.split():
                try:
                    val = float(token)
                    if any(u in desc for u in ["tb", "terabyte"]):
                        storage_gb = val * 1024
                    elif any(u in desc for u in ["gb", "gigabyte"]):
                        storage_gb = val
                    elif any(u in desc for u in ["mb", "megabyte"]):
                        storage_gb = val / 1024
                    else:
                        storage_gb = val
                    break
                except ValueError:
                    continue

        # Compute keywords
        if any(w in desc for w in [
            "compute", "train", "inference", "ml", "ai", "gpu",
            "process", "run", "execute", "model",
        ]):
            compute_hours = 10.0  # default
            for token in desc.split():
                try:
                    val = float(token)
                    if "day" in desc:
                        compute_hours = val * 24
                    elif "week" in desc:
                        compute_hours = val * 168
                    elif "hour" in desc:
                        compute_hours = val
                    else:
                        compute_hours = val
                    break
                except ValueError:
                    continue

        # If nothing detected, give a basic estimate
        if storage_gb == 0 and compute_hours == 0:
            storage_gb = 5.0
            compute_hours = 2.0

        avg_storage_price = 0.045
        avg_compute_price = 0.11

        storage_cost = storage_gb * avg_storage_price
        compute_cost = compute_hours * avg_compute_price
        total = storage_cost + compute_cost

        return {
            "storage_gb": storage_gb,
            "compute_hours": compute_hours,
            "storage_cost": round(storage_cost, 4),
            "compute_cost": round(compute_cost, 4),
            "total_cost": round(total, 4),
            "currency": "0G",
        }
