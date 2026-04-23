"""Wallet service - manages embedded wallets on 0G mainnet.

All web3 calls are wrapped in asyncio.to_thread so they don't block
the Telegram event loop.
"""

import asyncio
import logging
from typing import Optional

from web3 import Web3
from eth_account import Account

from bot.config import config
from bot.db.database import Database
from bot.models.user import User
from bot.utils.encryption import WalletEncryption

logger = logging.getLogger(__name__)

GAS_LIMIT_NATIVE = 21_000
RECEIPT_POLL_ATTEMPTS = 30
RECEIPT_POLL_INTERVAL = 2.0


class WalletService:
    """Async-safe wallet service for 0G Network."""

    def __init__(self, db: Database):
        self.db = db
        self.w3 = Web3(Web3.HTTPProvider(config.OG_RPC_URL, request_kwargs={"timeout": 30}))

    async def get_or_create_user(
        self, telegram_id: int, username: Optional[str] = None
    ) -> User:
        user = await self.db.get_user(telegram_id)
        if user:
            return user

        acct = Account.create()
        encrypted_key = WalletEncryption.encrypt(acct.key.hex())

        user = User(
            telegram_id=telegram_id,
            username=username,
            wallet_address=acct.address,
            encrypted_private_key=encrypted_key,
        )
        user.id = await self.db.create_user(user)
        logger.info("Created wallet %s for user %s", acct.address, telegram_id)
        return user

    def get_private_key(self, user: User) -> str:
        if not user.encrypted_private_key:
            raise ValueError("User has no wallet")
        return WalletEncryption.decrypt(user.encrypted_private_key)

    async def get_balance(self, address: str) -> float:
        """Get balance in OG (native 0G token) as float."""
        try:
            checksum = Web3.to_checksum_address(address)
            balance_wei = await asyncio.to_thread(self.w3.eth.get_balance, checksum)
            return float(Web3.from_wei(balance_wei, "ether"))
        except Exception as e:
            logger.error("balance fetch failed %s: %s", address, e)
            return 0.0

    async def get_balance_wei(self, address: str) -> int:
        """Get raw balance in wei."""
        try:
            checksum = Web3.to_checksum_address(address)
            return await asyncio.to_thread(self.w3.eth.get_balance, checksum)
        except Exception as e:
            logger.error("balance_wei fetch failed %s: %s", address, e)
            return 0

    async def send_transaction(
        self, private_key: str, to: str, value_ether: float, data: bytes = b""
    ) -> str:
        """Build, sign, and broadcast a native value transfer. Returns tx hash."""

        def _build_sign():
            acct = Account.from_key(private_key)
            to_addr = Web3.to_checksum_address(to)
            nonce = self.w3.eth.get_transaction_count(acct.address)
            gas_price = int(self.w3.eth.gas_price * 1.1)

            tx = {
                "nonce": nonce,
                "to": to_addr,
                "value": Web3.to_wei(value_ether, "ether"),
                "gas": 100_000 if data else GAS_LIMIT_NATIVE,
                "gasPrice": gas_price,
                "chainId": config.OG_CHAIN_ID,
                "data": data,
            }
            try:
                tx["gas"] = int(self.w3.eth.estimate_gas(tx) * 1.2)
            except Exception:
                pass
            signed = self.w3.eth.account.sign_transaction(tx, private_key)
            return signed.raw_transaction

        raw = await asyncio.to_thread(_build_sign)
        tx_hash = await asyncio.to_thread(self.w3.eth.send_raw_transaction, raw)
        hash_hex = tx_hash.hex()
        return hash_hex if hash_hex.startswith("0x") else "0x" + hash_hex

    async def wait_for_confirmation(self, tx_hash: str) -> Optional[dict]:
        """Poll for receipt. Returns receipt dict or None on timeout."""
        for _ in range(RECEIPT_POLL_ATTEMPTS):
            try:
                receipt = await asyncio.to_thread(
                    self.w3.eth.get_transaction_receipt, tx_hash
                )
                if receipt is not None:
                    return dict(receipt)
            except Exception:
                pass
            await asyncio.sleep(RECEIPT_POLL_INTERVAL)
        return None

    def get_explorer_url(self, tx_hash: str) -> str:
        return f"{config.OG_EXPLORER}/tx/{tx_hash}"
