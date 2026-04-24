"""0G Compute CLI wrapper used for live market discovery."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path

from bot.config import config

CONFIG_DIR = Path.home() / ".0g-compute-cli"
CONFIG_PATH = CONFIG_DIR / "config.json"
NPX_FALLBACK = ["npx", "-y", "@0glabs/0g-serving-broker"]


def _command_prefix() -> list[str]:
    if config.OG_COMPUTE_CLI_BIN and shutil.which(config.OG_COMPUTE_CLI_BIN):
        return [config.OG_COMPUTE_CLI_BIN]
    return NPX_FALLBACK


def _ensure_cli_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "rpcEndpoint": config.OG_COMPUTE_CLI_RPC,
        "network": config.OG_COMPUTE_CLI_NETWORK,
    }
    if CONFIG_PATH.exists():
        try:
            current = json.loads(CONFIG_PATH.read_text())
        except Exception:
            current = {}
        current.update(payload)
        payload = current
    CONFIG_PATH.write_text(json.dumps(payload, indent=2))


async def _run_cli(*args: str, timeout: int = 25) -> str:
    _ensure_cli_config()
    process = await asyncio.create_subprocess_exec(
        *(_command_prefix() + list(args)),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "HOME": str(Path.home())},
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        raise RuntimeError("0G Compute CLI request timed out")
    output = stdout.decode().strip()
    error = stderr.decode().strip()
    if process.returncode != 0:
        raise RuntimeError(error or output or "0G Compute CLI command failed")
    return output or error or "No output returned."


async def get_network_status() -> str:
    return await _run_cli("show-network")


async def list_compute_providers() -> str:
    return await _run_cli("inference", "list-providers")


async def list_model_catalog() -> str:
    return await _run_cli("fine-tuning", "list-models")
