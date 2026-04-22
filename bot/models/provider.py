from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Provider:
    name: str
    provider_type: str  # "storage" or "compute"
    address: str
    price_per_unit: float  # per GB/month for storage, per vCPU-hour for compute
    total_capacity: float
    used_capacity: float = 0.0
    uptime_pct: float = 99.9
    region: str = "global"
    rating: float = 5.0
    is_active: bool = True
    endpoint: Optional[str] = None
    id: Optional[int] = field(default=None)

    @property
    def available_capacity(self) -> float:
        return self.total_capacity - self.used_capacity

    @classmethod
    def from_row(cls, row: dict) -> "Provider":
        return cls(
            id=row.get("id"),
            name=row["name"],
            provider_type=row["provider_type"],
            address=row["address"],
            price_per_unit=row["price_per_unit"],
            total_capacity=row["total_capacity"],
            used_capacity=row.get("used_capacity", 0.0),
            uptime_pct=row.get("uptime_pct", 99.9),
            region=row.get("region", "global"),
            rating=row.get("rating", 5.0),
            is_active=bool(row.get("is_active", True)),
            endpoint=row.get("endpoint"),
        )
