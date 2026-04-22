import aiosqlite
import logging
from typing import Optional

from bot.config import config
from bot.models.user import User
from bot.models.resource import Resource
from bot.models.provider import Provider

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.DATABASE_PATH
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._create_tables()
        await self._seed_providers()
        logger.info("Database connected and initialized")

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def _create_tables(self) -> None:
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                wallet_address TEXT,
                encrypted_private_key TEXT,
                is_node_operator INTEGER DEFAULT 0,
                node_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider_type TEXT NOT NULL,
                address TEXT NOT NULL,
                price_per_unit REAL NOT NULL,
                total_capacity REAL NOT NULL,
                used_capacity REAL DEFAULT 0,
                uptime_pct REAL DEFAULT 99.9,
                region TEXT DEFAULT 'global',
                rating REAL DEFAULT 5.0,
                is_active INTEGER DEFAULT 1,
                endpoint TEXT
            );

            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_type TEXT NOT NULL,
                provider_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                price_paid REAL NOT NULL,
                tx_hash TEXT,
                status TEXT DEFAULT 'active',
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            );

            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                merkle_root TEXT,
                tx_hash TEXT,
                status TEXT DEFAULT 'uploading',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                tx_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider_id INTEGER NOT NULL,
                job_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                tx_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            );
        """)
        await self._db.commit()

    async def _seed_providers(self) -> None:
        cursor = await self._db.execute("SELECT COUNT(*) FROM providers")
        row = await cursor.fetchone()
        if row[0] > 0:
            return

        seed_data = [
            ("0G Storage Alpha", "storage", "0x1a2b3c4d5e6f7890abcdef1234567890abcdef01",
             0.05, 10000.0, 3200.0, 99.95, "US-East", 4.8,
             "https://storage-alpha.0g.ai"),
            ("0G Storage Beta", "storage", "0x2b3c4d5e6f7890abcdef1234567890abcdef0102",
             0.04, 50000.0, 18000.0, 99.8, "EU-West", 4.6,
             "https://storage-beta.0g.ai"),
            ("0G Storage Gamma", "storage", "0x3c4d5e6f7890abcdef1234567890abcdef010203",
             0.06, 5000.0, 1200.0, 99.99, "Asia-SE", 4.9,
             "https://storage-gamma.0g.ai"),
            ("0G Storage Delta", "storage", "0x4d5e6f7890abcdef1234567890abcdef01020304",
             0.035, 100000.0, 62000.0, 99.7, "US-West", 4.5,
             "https://storage-delta.0g.ai"),
            ("0G Compute Node-1", "compute", "0x5e6f7890abcdef1234567890abcdef0102030405",
             0.12, 500.0, 180.0, 99.9, "US-East", 4.7,
             "https://compute-1.0g.ai"),
            ("0G Compute Node-2", "compute", "0x6f7890abcdef1234567890abcdef010203040506",
             0.10, 1000.0, 420.0, 99.85, "EU-West", 4.8,
             "https://compute-2.0g.ai"),
            ("0G Compute Node-3", "compute", "0x7890abcdef1234567890abcdef01020304050607",
             0.15, 200.0, 50.0, 99.95, "Asia-SE", 4.9,
             "https://compute-3.0g.ai"),
            ("0G Compute Node-4", "compute", "0x890abcdef1234567890abcdef0102030405060708",
             0.08, 2000.0, 1100.0, 99.6, "US-West", 4.4,
             "https://compute-4.0g.ai"),
        ]

        for row in seed_data:
            await self._db.execute(
                """INSERT INTO providers
                   (name, provider_type, address, price_per_unit, total_capacity,
                    used_capacity, uptime_pct, region, rating, endpoint)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                row,
            )
        await self._db.commit()
        logger.info("Seeded %d providers", len(seed_data))

    # ── User operations ──────────────────────────────────────────────

    async def get_user(self, telegram_id: int) -> Optional[User]:
        cursor = await self._db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return User.from_row(dict(row))
        return None

    async def create_user(self, user: User) -> int:
        cursor = await self._db.execute(
            """INSERT INTO users (telegram_id, username, wallet_address,
               encrypted_private_key, is_node_operator, node_address)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user.telegram_id,
                user.username,
                user.wallet_address,
                user.encrypted_private_key,
                int(user.is_node_operator),
                user.node_address,
            ),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def update_user(self, user: User) -> None:
        await self._db.execute(
            """UPDATE users SET username=?, wallet_address=?,
               encrypted_private_key=?, is_node_operator=?, node_address=?
               WHERE telegram_id=?""",
            (
                user.username,
                user.wallet_address,
                user.encrypted_private_key,
                int(user.is_node_operator),
                user.node_address,
                user.telegram_id,
            ),
        )
        await self._db.commit()

    # ── Provider operations ──────────────────────────────────────────

    async def get_providers(self, provider_type: Optional[str] = None) -> list[Provider]:
        if provider_type:
            cursor = await self._db.execute(
                "SELECT * FROM providers WHERE provider_type = ? AND is_active = 1",
                (provider_type,),
            )
        else:
            cursor = await self._db.execute(
                "SELECT * FROM providers WHERE is_active = 1"
            )
        rows = await cursor.fetchall()
        return [Provider.from_row(dict(r)) for r in rows]

    async def get_provider(self, provider_id: int) -> Optional[Provider]:
        cursor = await self._db.execute(
            "SELECT * FROM providers WHERE id = ?", (provider_id,)
        )
        row = await cursor.fetchone()
        if row:
            return Provider.from_row(dict(row))
        return None

    # ── Resource operations ──────────────────────────────────────────

    async def create_resource(self, resource: Resource) -> int:
        cursor = await self._db.execute(
            """INSERT INTO resources
               (user_id, resource_type, provider_id, amount, price_paid,
                tx_hash, status, expires_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                resource.user_id,
                resource.resource_type,
                resource.provider_id,
                resource.amount,
                resource.price_paid,
                resource.tx_hash,
                resource.status,
                resource.expires_at,
                resource.metadata,
            ),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_user_resources(
        self, user_id: int, status: Optional[str] = None
    ) -> list[Resource]:
        if status:
            cursor = await self._db.execute(
                "SELECT * FROM resources WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status),
            )
        else:
            cursor = await self._db.execute(
                "SELECT * FROM resources WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
        rows = await cursor.fetchall()
        return [Resource.from_row(dict(r)) for r in rows]

    async def update_resource_status(self, resource_id: int, status: str) -> None:
        await self._db.execute(
            "UPDATE resources SET status = ? WHERE id = ?", (status, resource_id)
        )
        await self._db.commit()

    # ── File operations ──────────────────────────────────────────────

    async def create_file(
        self, user_id: int, filename: str, file_size: int, merkle_root: str = "",
        tx_hash: str = "", status: str = "uploading"
    ) -> int:
        cursor = await self._db.execute(
            """INSERT INTO files (user_id, filename, file_size, merkle_root, tx_hash, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, filename, file_size, merkle_root, tx_hash, status),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_user_files(self, user_id: int) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT * FROM files WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def update_file_status(
        self, file_id: int, status: str, merkle_root: str = "", tx_hash: str = ""
    ) -> None:
        await self._db.execute(
            "UPDATE files SET status=?, merkle_root=?, tx_hash=? WHERE id=?",
            (status, merkle_root, tx_hash, file_id),
        )
        await self._db.commit()

    # ── Earnings operations ──────────────────────────────────────────

    async def add_earning(
        self, user_id: int, amount: float, source: str, tx_hash: str = ""
    ) -> int:
        cursor = await self._db.execute(
            "INSERT INTO earnings (user_id, amount, source, tx_hash) VALUES (?, ?, ?, ?)",
            (user_id, amount, source, tx_hash),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_user_earnings(self, user_id: int) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT * FROM earnings WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_earnings_summary(self, user_id: int) -> dict:
        cursor = await self._db.execute(
            """SELECT
                 COALESCE(SUM(amount), 0) as total,
                 COUNT(*) as count,
                 COALESCE(SUM(CASE WHEN created_at >= date('now', '-30 days')
                   THEN amount ELSE 0 END), 0) as last_30d
               FROM earnings WHERE user_id = ?""",
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row)

    # ── Job operations ───────────────────────────────────────────────

    async def create_job(
        self, user_id: int, provider_id: int, job_type: str, tx_hash: str = ""
    ) -> int:
        cursor = await self._db.execute(
            """INSERT INTO jobs (user_id, provider_id, job_type, status, tx_hash)
               VALUES (?, ?, ?, 'pending', ?)""",
            (user_id, provider_id, job_type, tx_hash),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_user_jobs(self, user_id: int) -> list[dict]:
        cursor = await self._db.execute(
            """SELECT j.*, p.name as provider_name
               FROM jobs j JOIN providers p ON j.provider_id = p.id
               WHERE j.user_id = ? ORDER BY j.created_at DESC""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def update_job_status(
        self, job_id: int, status: str, result: str = ""
    ) -> None:
        if status == "completed":
            await self._db.execute(
                "UPDATE jobs SET status=?, result=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
                (status, result, job_id),
            )
        else:
            await self._db.execute(
                "UPDATE jobs SET status=?, result=? WHERE id=?",
                (status, result, job_id),
            )
        await self._db.commit()
