import logging
from typing import Optional
from web3 import Web3
from eth_account import Account

from bot.config import config
from bot.db.database import Database
from bot.models.user import User
from bot.utils.encryption import WalletEncryption

logger = logging.getLogger(__name__)


class WalletService:
    def __init__(self, db: Database):
        self.db = db
        self.w3 = Web3(Web3.HTTPProvider(config.OG_RPC_URL))

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

    def get_balance(self, address: str) -> float:
        try:
            balance_wei = self.w3.eth.get_balance(
                Web3.to_checksum_address(address)
            )
            return float(Web3.from_wei(balance_wei, "ether"))
        except Exception as e:
            logger.error("Failed to fetch balance for %s: %s", address, e)
            return 0.0

    def send_transaction(
        self, private_key: str, to: str, value_ether: float, data: bytes = b""
    ) -> str:
        acct = Account.from_key(private_key)
        to_addr = Web3.to_checksum_address(to)
        nonce = self.w3.eth.get_transaction_count(acct.address)

        tx = {
            "nonce": nonce,
            "to": to_addr,
            "value": Web3.to_wei(value_ether, "ether"),
            "gas": 100000,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": config.OG_CHAIN_ID,
            "data": data,
        }

        try:
            tx["gas"] = self.w3.eth.estimate_gas(tx)
        except Exception:
            pass  # use default

        signed = self.w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    def get_explorer_url(self, tx_hash: str) -> str:
        return f"{config.OG_EXPLORER}/tx/{tx_hash}"
