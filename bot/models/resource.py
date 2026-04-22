from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Resource:
    user_id: int
    resource_type: str  # "storage" or "compute"
    provider_id: int
    amount: float  # GB for storage, vCPU-hours for compute
    price_paid: float  # in 0G tokens
    tx_hash: Optional[str] = None
    status: str = "active"  # active, expired, cancelled
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Optional[str] = None  # JSON string for extra info
    id: Optional[int] = field(default=None)

    @classmethod
    def from_row(cls, row: dict) -> "Resource":
        return cls(
            id=row.get("id"),
            user_id=row["user_id"],
            resource_type=row["resource_type"],
            provider_id=row["provider_id"],
            amount=row["amount"],
            price_paid=row["price_paid"],
            tx_hash=row.get("tx_hash"),
            status=row.get("status", "active"),
            expires_at=row.get("expires_at"),
            created_at=row.get("created_at"),
            metadata=row.get("metadata"),
        )
