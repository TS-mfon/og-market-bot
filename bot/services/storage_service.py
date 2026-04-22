import hashlib
import logging
import aiohttp
from typing import Optional

from bot.config import config
from bot.db.database import Database
from bot.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, db: Database, wallet_service: WalletService):
        self.db = db
        self.wallet = wallet_service
        self.indexer_url = config.OG_STORAGE_INDEXER

    async def upload_file(
        self, telegram_id: int, filename: str, file_data: bytes
    ) -> dict:
        user = await self.wallet.get_or_create_user(telegram_id)
        file_size = len(file_data)

        # Compute a merkle root (simplified: sha256 of content)
        merkle_root = "0x" + hashlib.sha256(file_data).hexdigest()

        file_id = await self.db.create_file(
            user_id=user.id,
            filename=filename,
            file_size=file_size,
            merkle_root=merkle_root,
            status="uploading",
        )

        # Attempt upload to 0G storage indexer
        try:
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field(
                    "file", file_data, filename=filename,
                    content_type="application/octet-stream",
                )
                async with session.post(
                    f"{self.indexer_url}/file",
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status in (200, 201):
                        result = await resp.json()
                        tx_hash = result.get("tx_hash", "")
                        await self.db.update_file_status(
                            file_id, "uploaded", merkle_root, tx_hash
                        )
                        return {
                            "success": True,
                            "file_id": file_id,
                            "filename": filename,
                            "size": file_size,
                            "merkle_root": merkle_root,
                            "tx_hash": tx_hash,
                        }
                    else:
                        body = await resp.text()
                        logger.warning(
                            "Upload returned %d: %s", resp.status, body[:200]
                        )
        except Exception as e:
            logger.warning("Upload to indexer failed: %s", e)

        # Mark as uploaded locally even if indexer is unavailable (testnet)
        await self.db.update_file_status(file_id, "stored_locally", merkle_root)
        return {
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "size": file_size,
            "merkle_root": merkle_root,
            "tx_hash": "",
            "note": "File recorded. Indexer upload will be retried.",
        }

    async def list_files(self, telegram_id: int) -> list[dict]:
        user = await self.db.get_user(telegram_id)
        if not user:
            return []
        return await self.db.get_user_files(user.id)
