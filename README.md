# OG Market Bot — 0G Mainnet Compute & Storage Marketplace

A production-grade Telegram bot for buying decentralized compute and storage on 0G Network mainnet (chain ID 480).

## Features

### Providers
- `/storage_providers` — List active storage providers with live chain metrics
- `/compute_providers` — List compute providers
- `/compare` — Side-by-side provider comparison

### Purchase
- `/buy_storage <provider_id> <gb> <months>` — Buy storage (real on-chain tx)
- `/buy_compute <provider_id> <hours>` — Buy compute
- `/estimate <description>` — Cost estimator

### Resources
- `/my_resources` — Your active purchases
- `/renew <resource_id>` — Renew a resource
- `/cancel <resource_id>` — Cancel

### Files
- `/upload` — Upload to 0G Storage (real indexer POST)
- `/files` — List uploaded files

### Jobs
- `/job_status <job_id>` — On-chain status check

### Operators
- `/earnings` — View node earnings
- `/earnings register <address>` — Register as operator

## Production Features

- Real on-chain purchases with balance check + receipt polling
- Async/await throughout (all web3 calls wrapped in `asyncio.to_thread`)
- Live provider data (chain activity determines active/inactive)
- Auto-renewal via APScheduler
- Incoming tx notifications for operators
- Rate limiting
- Structured JSON logging
- Multi-stage Docker build with non-root user
- Fernet-encrypted private keys

## Setup

```bash
cp .env.example .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
pip install -r requirements.txt
python -m bot.main
```

## Deploy to Render

1. Create Web Service from this repo
2. Docker runtime
3. Set env vars from `.env.example`
4. Deploy

## License

MIT
