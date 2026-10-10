import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logger import Logger  # noqa: E402


def test_bot_logger_falls_back_when_repo_log_directory_is_not_writable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    blocked_dir = tmp_path / "logs"
    blocked_dir.mkdir()
    blocked_dir.chmod(0o555)

    try:
        logger = Logger("fallback-bot")
        logger.info("can write somewhere")
    finally:
        blocked_dir.chmod(0o755)
        logging.getLogger("BotLogger_fallback-bot").handlers.clear()

    assert logger.log_dir != str(blocked_dir)
