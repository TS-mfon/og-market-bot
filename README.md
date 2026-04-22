# 0G Market Bot

Telegram marketplace bot for 0G compute and storage resources.

## Features

- Browse storage and compute providers on the 0G network
- Compare providers side-by-side with formatted tables
- Purchase storage and compute resources via embedded wallets
- Upload and download files to/from 0G storage
- Track job status for compute workloads
- Monitor earnings for node operators
- Estimate costs for workloads using natural language descriptions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env`:
```
TELEGRAM_BOT_TOKEN=<your-bot-token>
OG_RPC_URL=https://evmrpc-testnet.0g.ai
OG_STORAGE_INDEXER=https://indexer-storage-testnet-turbo.0g.ai
OG_COMPUTE_API=https://compute-testnet.0g.ai
WALLET_ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
```

3. Run:
```bash
python -m bot.main
```

## Docker

```bash
docker build -t og-market-bot .
docker run --env-file .env og-market-bot
```

## Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and overview |
| `/help` | List all commands |
| `/storage_providers` | Browse storage providers |
| `/compute_providers` | Browse compute providers |
| `/buy_storage` | Purchase storage capacity |
| `/buy_compute` | Purchase compute resources |
| `/my_resources` | View your active resources |
| `/renew` | Renew a resource subscription |
| `/cancel` | Cancel a resource |
| `/upload` | Upload a file to 0G storage |
| `/files` | List your uploaded files |
| `/job_status` | Check compute job status |
| `/earnings` | View node operator earnings |
| `/compare` | Compare providers side-by-side |
| `/estimate` | Estimate cost for a workload |
