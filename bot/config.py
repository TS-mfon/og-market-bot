import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    OG_RPC_URL: str = os.getenv("OG_RPC_URL", "https://evmrpc-testnet.0g.ai")
    OG_STORAGE_INDEXER: str = os.getenv(
        "OG_STORAGE_INDEXER", "https://indexer-storage-testnet-turbo.0g.ai"
    )
    OG_COMPUTE_API: str = os.getenv(
        "OG_COMPUTE_API", "https://compute-testnet.0g.ai"
    )
    WALLET_ENCRYPTION_KEY: str = os.getenv("WALLET_ENCRYPTION_KEY", "")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "og_market.db")
    OG_CHAIN_ID: int = int(os.getenv("OG_CHAIN_ID", "16600"))
    OG_EXPLORER: str = os.getenv(
        "OG_EXPLORER", "https://chainscan-newton.0g.ai"
    )


config = Config()
