# 0G Market Bot

0G Market Bot is a Telegram-native marketplace surface for the 0G mainnet stack. It lets users inspect 0G storage and compute routes, estimate workloads, upload files, and submit payable purchase intents through an on-chain market contract.

## Hackathon Summary

- Project name: `0G Market Bot`
- One-line description: `Telegram marketplace for 0G mainnet that exposes storage and compute routes, pricing flows, and contract-backed purchase intents.`
- Prize track fit:
  - `Track 2: Agentic Trading Arena (Verifiable Finance)`
  - `Track 3: Agentic Economy & Autonomous Applications`
- 0G components used:
  - `0G Chain`
  - `0G Storage`
  - `0G Compute`

## What It Does

The bot acts as a conversational market interface for 0G:

- shows 0G storage entrypoints and compute network status
- discovers live compute provider output through the 0G Compute CLI
- estimates workload costs from plain-language prompts
- uploads files to 0G Storage
- tracks local resource purchases and job records
- routes storage and compute purchases into a dedicated 0G mainnet contract

## Problem It Solves

0G has powerful infra, but discovery and purchase flows are still fragmented across wallets, explorers, CLI tools, and storage endpoints. This bot compresses those flows into one interface and leaves verifiable on-chain purchase records behind.

## 0G Integration Proof

- Mainnet contract: `0x6Eea20692c0f1E0B3400b71a849c4DFAa169E14D`
- Explorer: `https://chainscan.0g.ai/address/0x6Eea20692c0f1E0B3400b71a849c4DFAa169E14D`
- Deployment tx: `https://chainscan.0g.ai/tx/0xf306a65590c93ef1705832f6279cfd2fb364c11d987fdd6413fc05801ba5a56e`
- Contract role:
  - `buyStorage(...)` records payable storage purchase intents
  - `buyCompute(...)` records payable compute purchase intents

## Commands

- `/start` wallet creation and overview
- `/commands` command list without rerunning `/start`
- `/help` detailed guide
- `/stack` current 0G mainnet stack configuration used by the bot
- `/storage_providers` storage stack summary plus the bot purchase routes
- `/compute_providers` live compute network output plus the bot purchase routes
- `/compute_models` 0G Compute model catalog
- `/compare <id1> <id2>` compare bot purchase routes
- `/buy_storage <provider_id> <gb> [months]` buy storage through the market contract
- `/buy_compute <provider_id> <hours>` buy compute through the market contract
- `/estimate <description>` estimate storage and compute cost
- `/my_resources` list current resources
- `/upload` upload to 0G Storage
- `/files` list uploaded files
- `/job_status` inspect job records
- `/earnings` view operator earnings

## Architecture

- Telegram interface:
  - handler-driven command surface in `bot/handlers`
- On-chain settlement:
  - Web3.py wallet service on 0G mainnet
  - `OGMarketBotHub.sol` for contract-backed purchase intents
- Live compute discovery:
  - `0g-compute-cli` or `npx @0glabs/0g-serving-broker`
- Storage:
  - `OG_STORAGE_INDEXER` upload path
- Persistence:
  - SQLite for users, providers, resources, files, and jobs

## Local Run

```bash
cp .env.example .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
pip install -r requirements.txt
python -m bot.main
```

Required env values:

- `TELEGRAM_BOT_TOKEN`
- `WALLET_ENCRYPTION_KEY`

Mainnet env defaults already included:

- `OG_RPC_URL=https://evmrpc.0g.ai`
- `OG_CHAIN_ID=16661`
- `OG_STORAGE_INDEXER=https://indexer-storage.0g.ai`
- `OG_MARKET_HUB_ADDRESS=0x6Eea20692c0f1E0B3400b71a849c4DFAa169E14D`

## Docker / Render

```bash
docker build -t og-market-bot .
docker run --env-file .env -p 10000:10000 og-market-bot
```

Render notes:

- Docker image installs Node.js and the 0G Compute CLI fallback
- health endpoint is exposed on `/`
- storage and compute purchase routes rely on `OG_MARKET_HUB_ADDRESS`

## Repository

- GitHub: `https://github.com/TS-mfon/og-market-bot`

## Reviewer Notes

- The bot exposes live compute discovery and bot-managed settlement separately on purpose
- `/compute_providers` shows live network output and then the purchase routes the bot can actually execute
- `/buy_storage` and `/buy_compute` submit value-bearing calls to the market contract, leaving explorer-verifiable activity

## Source Layout

- `bot/main.py` bot entrypoint
- `bot/handlers` Telegram command surface
- `bot/services` wallet, provider, purchase, storage, and CLI integrations
- `contracts/OGMarketBotHub.sol` 0G mainnet contract source

## License

MIT
