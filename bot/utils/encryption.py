import logging
from cryptography.fernet import Fernet
from bot.config import config

logger = logging.getLogger(__name__)


class WalletEncryption:
    _fernet: Fernet = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            key = config.WALLET_ENCRYPTION_KEY
            if key:
                try:
                    cls._fernet = Fernet(
                        key.encode() if isinstance(key, str) else key
                    )
                except (ValueError, Exception) as e:
                    logger.warning(
                        "Invalid WALLET_ENCRYPTION_KEY, generating new one: %s", e
                    )
                    cls._fernet = Fernet(Fernet.generate_key())
            else:
                logger.warning(
                    "No WALLET_ENCRYPTION_KEY set, generating ephemeral key. "
                    "Set this in .env for persistent wallet encryption."
                )
                cls._fernet = Fernet(Fernet.generate_key())
        return cls._fernet

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        f = cls._get_fernet()
        return f.encrypt(plaintext.encode()).decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        f = cls._get_fernet()
        return f.decrypt(ciphertext.encode()).decode()
