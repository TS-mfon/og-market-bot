from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
    wallet_address: Optional[str] = None
    encrypted_private_key: Optional[str] = None
    is_node_operator: bool = False
    node_address: Optional[str] = None
    created_at: Optional[str] = None
    id: Optional[int] = field(default=None)

    @classmethod
    def from_row(cls, row: dict) -> "User":
        return cls(
            id=row.get("id"),
            telegram_id=row["telegram_id"],
            username=row.get("username"),
            wallet_address=row.get("wallet_address"),
            encrypted_private_key=row.get("encrypted_private_key"),
            is_node_operator=bool(row.get("is_node_operator", False)),
            node_address=row.get("node_address"),
            created_at=row.get("created_at"),
        )
