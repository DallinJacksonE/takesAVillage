import json
import os
from pathlib import Path
from typing import Any

from service.db.facade import DatabaseFacade
from service.db.memory import InMemoryDB
from service.db.mysql import MySQLDB
from service.logging import BackendLogger

logger = BackendLogger("db")


def load_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[1] / "config.json"
    config: dict[str, Any] = {"db": {}, "flask": {}}
    try:
        config.update(json.loads(config_path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        logger.warning("config.json not found, relying on environment variables.")
    config.setdefault("db", {})
    database = config["db"]
    database["host"] = os.environ.get("DB_HOST", database.get("host", "127.0.0.1"))
    database["user"] = os.environ.get("DB_USER", database.get("user", "village"))
    database["password"] = os.environ.get("DB_PASSWORD", database.get("password", "village_db"))
    database["database"] = os.environ.get("DB_NAME", database.get("database", "village_db"))
    config["db_type"] = os.environ.get(
        "DB_TYPE", config.get("db_type", "mysql")
    ).strip().lower()
    return config


def get_database(config: dict[str, Any] | None = None):
    resolved = config or load_config()
    if resolved.get("db_type") == "memory":
        return InMemoryDB()
    return DatabaseFacade(MySQLDB(resolved["db"]))
