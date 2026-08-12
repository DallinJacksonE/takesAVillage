import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def get_service_config() -> dict[str, Any]:
    config_path = Path(os.environ.get(
        "SERVICE_CONFIG_PATH",
        Path(__file__).resolve().parents[1] / "service" / "config.json",
    ))
    try:
        value = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Unable to load bot service configuration") from exc
    bots = value.get("bots")
    if not isinstance(bots, dict):
        raise RuntimeError("Bot service configuration is missing 'bots'")
    for key in ("secret", "httpUrl", "gameServerHttpUrl", "gameServerWsUrl"):
        if not isinstance(bots.get(key), str) or not bots[key]:
            raise RuntimeError(f"Bot service configuration is missing bots.{key}")
    return value


def get_bot_config() -> dict[str, str]:
    return get_service_config()["bots"]
